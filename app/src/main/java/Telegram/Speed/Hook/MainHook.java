package Telegram.Speed.Hook;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.Toast;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import io.github.libxposed.api.XposedInterface.ExceptionMode;
import io.github.libxposed.api.XposedModule;
import io.github.libxposed.api.XposedModuleInterface.ModuleLoadedParam;
import io.github.libxposed.api.XposedModuleInterface.PackageReadyParam;

/**
 * Modern libxposed entry point for Telegram Speed Hook.
 *
 * <p>The module intentionally performs the same post-updateParams tuning as the
 * legacy implementation, but uses API 102's interceptor-chain hook model and
 * ordinary Java reflection instead of XposedHelpers/XC_MethodHook.</p>
 */
public final class MainHook extends XposedModule {
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

    private static volatile long speedUpShownAtMs;

    @Override
    public void onModuleLoaded(ModuleLoadedParam param) {
        log(Log.INFO, TAG,
                "module loaded in process=" + param.getProcessName()
                        + " framework=" + getFrameworkName()
                        + " " + getFrameworkVersion()
                        + " api=" + getApiVersion());
    }

    @Override
    public void onPackageReady(PackageReadyParam param) {
        String packageName = param.getPackageName();
        if (!param.isFirstPackage() || !SUPPORTED_PACKAGES.contains(packageName)) {
            return;
        }

        log(Log.INFO, TAG, "preparing hook for " + packageName);

        try {
            Class<?> operationClass = Class.forName(
                    FILE_LOAD_OPERATION_CLASS,
                    false,
                    param.getClassLoader()
            );
            Method updateParams = operationClass.getDeclaredMethod("updateParams");
            updateParams.setAccessible(true);

            hook(updateParams)
                    .setExceptionMode(ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        // Preserve legacy afterHookedMethod semantics: Telegram runs first.
                        Object result = chain.proceed();
                        Object operation = chain.getThisObject();
                        if (operation != null && applySpeedParams(operation)) {
                            maybeShowActivationToast(operation);
                        }
                        return result;
                    });

            log(Log.INFO, TAG,
                    "hooked " + FILE_LOAD_OPERATION_CLASS + "#updateParams via libxposed API 102");
        } catch (Throwable t) {
            log(Log.ERROR, TAG,
                    "failed to hook " + FILE_LOAD_OPERATION_CLASS + "#updateParams", t);
        }
    }

    private boolean applySpeedParams(Object operation) {
        try {
            boolean changed = SpeedPolicy.apply(operation);
            if (changed) {
                log(Log.INFO, TAG,
                        "speed params applied"
                                + " size=" + safeGetLongField(operation, "totalBytesCount", 0L)
                                + " chunkBig=" + SpeedPolicy.DOWNLOAD_CHUNK_SIZE_BIG
                                + " requestsBig=" + SpeedPolicy.MAX_DOWNLOAD_REQUESTS_BIG
                                + " maxCdnParts=" + SpeedPolicy.MAX_CDN_PARTS);
            }
            return changed;
        } catch (Throwable t) {
            log(Log.ERROR, TAG, "failed to apply speed params", t);
            return false;
        }
    }

    private long safeGetLongField(Object object, String fieldName, long fallback) {
        try {
            return findField(object.getClass(), fieldName).getLong(object);
        } catch (Throwable ignored) {
            return fallback;
        }
    }

    private boolean safeGetBooleanField(Object object, String fieldName, boolean fallback) {
        try {
            return findField(object.getClass(), fieldName).getBoolean(object);
        } catch (Throwable ignored) {
            return fallback;
        }
    }

    private static Field findField(Class<?> type, String fieldName) throws NoSuchFieldException {
        Class<?> current = type;
        while (current != null) {
            try {
                Field field = current.getDeclaredField(fieldName);
                field.setAccessible(true);
                return field;
            } catch (NoSuchFieldException ignored) {
                current = current.getSuperclass();
            }
        }
        throw new NoSuchFieldException(type.getName() + "." + fieldName);
    }

    private void maybeShowActivationToast(Object operation) {
        long fileSize = safeGetLongField(operation, "totalBytesCount", 0L);
        long now = System.currentTimeMillis();

        synchronized (MainHook.class) {
            if (fileSize <= BIG_FILE_SIZE_FROM
                    || now - speedUpShownAtMs <= TOAST_THROTTLE_MS) {
                return;
            }
            speedUpShownAtMs = now;
        }

        new Handler(Looper.getMainLooper()).post(() -> {
            try {
                Context context = currentApplicationContext();
                if (context == null) {
                    log(Log.DEBUG, TAG, "activation toast skipped: no application context yet");
                    return;
                }
                Toast.makeText(
                        context,
                        "Speed Boost Activated\nTelegram/Nullgram speed params applied",
                        Toast.LENGTH_SHORT
                ).show();
            } catch (Throwable t) {
                log(Log.WARN, TAG, "failed to show activation toast", t);
            }
        });
    }

    private Context currentApplicationContext() {
        try {
            // Avoid the legacy AndroidAppHelper dependency. ActivityThread is used only
            // as an optional best-effort source for a Toast context; hook correctness
            // never depends on it.
            Class<?> activityThread = Class.forName("android.app.ActivityThread");
            Method currentApplication = activityThread.getDeclaredMethod("currentApplication");
            currentApplication.setAccessible(true);
            Object application = currentApplication.invoke(null);
            return application instanceof Context ? (Context) application : null;
        } catch (Throwable t) {
            log(Log.DEBUG, TAG, "application context unavailable", t);
            return null;
        }
    }
}
