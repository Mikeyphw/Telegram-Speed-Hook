package Telegram.Speed.Hook;

import java.lang.reflect.Field;

/** Pure-Java, side-effect-bounded parameters for Telegram/Nullgram file downloads. */
final class SpeedPolicy {
    static final int BIG_FILE_SIZE_FROM = 5 * 1024 * 1024;
    static final int DOWNLOAD_CHUNK_SIZE_BIG = 1024 * 1024;
    static final int MAX_DOWNLOAD_REQUESTS_BIG = 12;
    static final long DEFAULT_MAX_FILE_SIZE = 1024L * 1024L * 2000L;
    static final int MAX_CDN_PARTS = (int) (DEFAULT_MAX_FILE_SIZE / DOWNLOAD_CHUNK_SIZE_BIG);

    private SpeedPolicy() { }

    static boolean apply(Object operation) {
        if (operation == null || shouldSkip(operation)) {
            return false;
        }
        boolean changed = false;
        changed |= setInt(operation, "bigFileSizeFrom", BIG_FILE_SIZE_FROM);
        changed |= setInt(operation, "downloadChunkSizeBig", DOWNLOAD_CHUNK_SIZE_BIG);
        changed |= setInt(operation, "maxDownloadRequestsBig", MAX_DOWNLOAD_REQUESTS_BIG);
        changed |= setInt(operation, "maxCdnParts", Math.max(1, MAX_CDN_PARTS));
        return changed;
    }

    static boolean shouldSkip(Object operation) {
        long size = getLong(operation, "totalBytesCount", 0L);
        return (size > 0 && size < BIG_FILE_SIZE_FROM)
                || getBoolean(operation, "forceSmallChunk", false)
                || getBoolean(operation, "isPreloadVideoOperation", false)
                || getBoolean(operation, "isStream", false);
    }

    private static boolean setInt(Object target, String key, int value) {
        try {
            Field field = field(target.getClass(), key);
            if (field.getInt(target) == value) {
                return false;
            }
            field.setInt(target, value);
            return true;
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            // Telegram forks may lack or change a field. Preserve the operation.
            return false;
        }
    }

    private static long getLong(Object target, String key, long fallback) {
        try {
            return field(target.getClass(), key).getLong(target);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return fallback;
        }
    }

    private static boolean getBoolean(Object target, String key, boolean fallback) {
        try {
            return field(target.getClass(), key).getBoolean(target);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return fallback;
        }
    }

    private static Field field(Class<?> type, String key) throws NoSuchFieldException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
                Field field = current.getDeclaredField(key);
                field.setAccessible(true);
                return field;
            } catch (NoSuchFieldException ignored) {
                // A protected inherited Telegram field is also supported.
            }
        }
        throw new NoSuchFieldException(key);
    }
}
