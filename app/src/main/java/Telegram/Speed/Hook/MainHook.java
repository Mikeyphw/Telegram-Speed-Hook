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
    private static final int MAX_DOWNLOAD_REQUESTS = 12;
    private static final int MAX_DOWNLOAD_REQUESTS_BIG = 12;

    private static final long DEFAULT_MAX_FILE_SIZE = 1024L * 1024L * 2000L;
    private static final long MIN_TOAST_FILE_SIZE = 5L * 1024L * 1024L;
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
                            applySpeedParams(param);
                            maybeShowActivationToast(param);
                        }
                    }
            );

            XposedBridge.log(TAG + ": hooked " + FILE_LOAD_OPERATION_CLASS + "#updateParams");
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": failed to hook " + FILE_LOAD_OPERATION_CLASS + "#updateParams");
            XposedBridge.log(t);
        }
    }

    private static void applySpeedParams(XC_MethodHook.MethodHookParam param) {
        try {
            int maxCdnParts = (int) (DEFAULT_MAX_FILE_SIZE / DOWNLOAD_CHUNK_SIZE_BIG);

            XposedHelpers.setIntField(param.thisObject, "downloadChunkSizeBig", DOWNLOAD_CHUNK_SIZE_BIG);
            XposedHelpers.setIntField(param.thisObject, "maxDownloadRequests", MAX_DOWNLOAD_REQUESTS);
            XposedHelpers.setIntField(param.thisObject, "maxDownloadRequestsBig", MAX_DOWNLOAD_REQUESTS_BIG);
            XposedHelpers.setIntField(param.thisObject, "maxCdnParts", maxCdnParts);
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": failed to apply speed params");
            XposedBridge.log(t);
        }
    }

    private static void maybeShowActivationToast(XC_MethodHook.MethodHookParam param) {
        try {
            long fileSize = XposedHelpers.getLongField(param.thisObject, "totalBytesCount");
            long now = System.currentTimeMillis();

            if (fileSize <= MIN_TOAST_FILE_SIZE || now - speedUpShownAtMs <= TOAST_THROTTLE_MS) {
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
