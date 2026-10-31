package Telegram.Speed.Hook;

import org.junit.Test;
import static org.junit.Assert.*;

/** Exercises the production policy, not a duplicated test-only implementation. */
public final class SpeedPolicyTest {
    private static class BaseOperation {
        private long totalBytesCount = 8L * 1024 * 1024;
        private boolean forceSmallChunk;
        private boolean isPreloadVideoOperation;
        private boolean isStream;
    }
    private static final class Operation extends BaseOperation {
        private int bigFileSizeFrom;
        private int downloadChunkSizeBig;
        private int maxDownloadRequestsBig;
        private int maxCdnParts;
    }
    private static final class PartialOperation {
        private long totalBytesCount = 10L * 1024 * 1024;
        private int maxDownloadRequestsBig;
        private String downloadChunkSizeBig = "fork-field";
    }

    @Test public void bigFileGetsEveryParameter() {
        Operation op = new Operation();
        assertTrue(SpeedPolicy.apply(op));
        assertEquals(5 * 1024 * 1024, op.bigFileSizeFrom);
        assertEquals(1024 * 1024, op.downloadChunkSizeBig);
        assertEquals(12, op.maxDownloadRequestsBig);
        assertEquals(2000, op.maxCdnParts);
    }
    @Test public void belowThresholdSkipsWithoutMutation() {
        Operation op = new Operation();
        ((BaseOperation) op).totalBytesCount = SpeedPolicy.BIG_FILE_SIZE_FROM - 1;
        assertFalse(SpeedPolicy.apply(op));
        assertEquals(0, op.maxDownloadRequestsBig);
    }
    @Test public void exactThresholdIsEligible() {
        Operation op = new Operation();
        ((BaseOperation) op).totalBytesCount = SpeedPolicy.BIG_FILE_SIZE_FROM;
        assertTrue(SpeedPolicy.apply(op));
    }
    @Test public void unknownSizeFollowsLegacyDefault() {
        Operation op = new Operation();
        ((BaseOperation) op).totalBytesCount = 0;
        assertTrue(SpeedPolicy.apply(op));
    }
    @Test public void forceSmallChunkNeverMutates() {
        Operation op = new Operation();
        ((BaseOperation) op).forceSmallChunk = true;
        assertFalse(SpeedPolicy.apply(op));
        assertEquals(0, op.maxCdnParts);
    }
    @Test public void preloadNeverMutates() {
        Operation op = new Operation();
        ((BaseOperation) op).isPreloadVideoOperation = true;
        assertFalse(SpeedPolicy.apply(op));
    }
    @Test public void streamNeverMutates() {
        Operation op = new Operation();
        ((BaseOperation) op).isStream = true;
        assertFalse(SpeedPolicy.apply(op));
    }
    @Test public void repeatedApplicationIsIdempotent() {
        Operation op = new Operation();
        assertTrue(SpeedPolicy.apply(op));
        assertFalse(SpeedPolicy.apply(op));
    }
    @Test public void absentOrWronglyTypedForkFieldsFailOpenSafely() {
        PartialOperation op = new PartialOperation();
        assertTrue(SpeedPolicy.apply(op));
        assertEquals(12, op.maxDownloadRequestsBig);
        assertEquals("fork-field", op.downloadChunkSizeBig);
        assertFalse(SpeedPolicy.apply(op));
    }
    @Test public void nullOperationIsIgnored() {
        assertFalse(SpeedPolicy.apply(null));
    }
}
