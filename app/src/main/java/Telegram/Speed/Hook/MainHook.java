package Telegram.Speed.Hook;

import android.app.AndroidAppHelper;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class MainHook implements IXposedHookLoadPackage {
    private static final String TAG = "TgSpeedHook";

    private static final String TELEGRAM_PACKAGE = "org.telegram.messenger";
    private static final String NULLGRAM_PACKAGE = "top.qwq2333.nullgram";

    private static final String FILE_LOAD_OPERATION_CLASS =
            "org.telegram.messenger.FileLoadOperation";

    private static final Set<String> SUPPORTED_PACKAGES = new HashSet<>(
            Arrays.asList(TELEGRAM_PACKAGE, NULLGRAM_PACKAGE)
    );

    private static final int DOWNLOAD_CHUNK_SIZE_BIG = 1024 * 1024; // 1 MiB
    private static final int MAX_DOWNLOAD_REQUESTS_BIG = 12;

    private static final int BIG_FILE_SIZE_FROM = 5 * 1024 * 1024;
    private static final long DEFAULT_MAX_FILE_SIZE = 1024L * 1024L * 2000L;
    private static final long TOAST_THROTTLE_MS = 2L * 60L * 1000L;

    private static long speedUpShownAtMs = 0L;

    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam lpparam) {
        if (!SUPPORTED_PACKAGES.contains(lpparam.packageName)) {
            return;
        }

        XposedBridge.log(TAG + ": loading for " + lpparam.packageName);

        try {
            XposedHelpers.findAndHookMethod(
                    FILE_LOAD_OPERATION_CLASS,
                    lpparam.classLoader,
                    "updateParams",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (applySpeedParams(param)) {
                                maybeShowActivationToast(param);
                            }
                        }
                    }
            );

            XposedBridge.log(TAG + ": hooked " + FILE_LOAD_OPERATION_CLASS + "#updateParams");
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": failed to hook " + FILE_LOAD_OPERATION_CLASS + "#updateParams");
            XposedBridge.log(t);
        }
    }

    private static boolean applySpeedParams(XC_MethodHook.MethodHookParam param) {
        try {
            Object operation = param.thisObject;

            if (shouldSkipOperation(operation)) {
                return false;
            }

            int maxCdnParts = Math.max(1, (int) (DEFAULT_MAX_FILE_SIZE / DOWNLOAD_CHUNK_SIZE_BIG));

            boolean changed = false;
            changed |= safeSetIntField(operation, "bigFileSizeFrom", BIG_FILE_SIZE_FROM);
            changed |= safeSetIntField(operation, "downloadChunkSizeBig", DOWNLOAD_CHUNK_SIZE_BIG);
            changed |= safeSetIntField(operation, "maxDownloadRequestsBig", MAX_DOWNLOAD_REQUESTS_BIG);
            changed |= safeSetIntField(operation, "maxCdnParts", maxCdnParts);

            if (changed) {
                XposedBridge.log(TAG + ": speed params applied"
                        + " size=" + safeGetLongField(operation, "totalBytesCount", 0L)
                        + " chunkBig=" + DOWNLOAD_CHUNK_SIZE_BIG
                        + " requestsBig=" + MAX_DOWNLOAD_REQUESTS_BIG
                        + " maxCdnParts=" + maxCdnParts);
            }

            return changed;
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": failed to apply speed params");
            XposedBridge.log(t);
            return false;
        }
    }

    private static boolean shouldSkipOperation(Object operation) {
        long size = safeGetLongField(operation, "totalBytesCount", 0L);

        if (size > 0 && size < BIG_FILE_SIZE_FROM) {
            return true;
        }

        return safeGetBooleanField(operation, "forceSmallChunk", false)
                || safeGetBooleanField(operation, "isPreloadVideoOperation", false)
                || safeGetBooleanField(operation, "isStream", false);
    }

    private static boolean safeSetIntField(Object object, String fieldName, int value) {
        try {
            XposedHelpers.setIntField(object, fieldName, value);
            return true;
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": could not set " + fieldName);
            XposedBridge.log(t);
            return false;
        }
    }

    private static long safeGetLongField(Object object, String fieldName, long fallback) {
        try {
            return XposedHelpers.getLongField(object, fieldName);
        } catch (Throwable ignored) {
            return fallback;
        }
    }

    private static boolean safeGetBooleanField(Object object, String fieldName, boolean fallback) {
        try {
            return XposedHelpers.getBooleanField(object, fieldName);
        } catch (Throwable ignored) {
            return fallback;
        }
    }

    private static void maybeShowActivationToast(XC_MethodHook.MethodHookParam param) {
        try {
            long fileSize = safeGetLongField(param.thisObject, "totalBytesCount", 0L);
            long now = System.currentTimeMillis();

            if (fileSize <= BIG_FILE_SIZE_FROM || now - speedUpShownAtMs <= TOAST_THROTTLE_MS) {
                return;
            }

            speedUpShownAtMs = now;

            new Handler(Looper.getMainLooper()).post(() -> {
                try {
                    Toast.makeText(
                            AndroidAppHelper.currentApplication(),
                            "Speed Boost Activated\nNullgram/Telegram speed params applied",
                            Toast.LENGTH_SHORT
                    ).show();
                } catch (Throwable t) {
                    XposedBridge.log(TAG + ": failed to show activation toast");
                    XposedBridge.log(t);
                }
            });
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": failed while checking file size");
            XposedBridge.log(t);
        }
    }
}
