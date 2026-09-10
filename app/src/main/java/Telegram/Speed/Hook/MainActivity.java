package Telegram.Speed.Hook;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.IOException;
import java.util.zip.ZipFile;

public class MainActivity extends Activity {
    private static final String JAVA_ENTRY = "META-INF/xposed/java_init.list";
    private static final String MODULE_PROP = "META-INF/xposed/module.prop";
    private static final String SCOPE_LIST = "META-INF/xposed/scope.list";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int padding = dp(24);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_VERTICAL);
        root.setPadding(padding, padding, padding, padding);

        TextView title = new TextView(this);
        title.setText("Telegram Speed Hook");
        title.setTextSize(24);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(12));

        MetadataStatus metadata = inspectInstalledApk();

        TextView body = new TextView(this);
        body.setText(
                "Modern libxposed API 102 module\n\n"
                        + "Installed APK metadata:\n"
                        + "• java_init.list: " + state(metadata.javaEntry) + "\n"
                        + "• module.prop: " + state(metadata.moduleProp) + "\n"
                        + "• scope.list: " + state(metadata.scopeList) + "\n"
                        + "• legacy assets/xposed_init: intentionally removed\n\n"
                        + "Static scopes:\n"
                        + "• org.telegram.messenger\n"
                        + "• top.qwq2333.nullgram\n\n"
                        + "After installing, enable this module in an LSPosed/libxposed API 102 "
                        + "compatible framework, select Telegram or Nullgram, force-stop the target, "
                        + "then reopen it.\n\n"
                        + "Logs:\n"
                        + "adb logcat -v time | grep TgSpeedHook"
                        + (metadata.error == null ? "" : "\n\nAPK inspection error: " + metadata.error)
        );
        body.setTextSize(15);

        root.addView(title, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        ));
        root.addView(body, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        ));

        setContentView(root);
    }

    private MetadataStatus inspectInstalledApk() {
        try (ZipFile apk = new ZipFile(getApplicationInfo().sourceDir)) {
            return new MetadataStatus(
                    apk.getEntry(JAVA_ENTRY) != null,
                    apk.getEntry(MODULE_PROP) != null,
                    apk.getEntry(SCOPE_LIST) != null,
                    null
            );
        } catch (IOException e) {
            return new MetadataStatus(false, false, false, e.getClass().getSimpleName());
        }
    }

    private static String state(boolean present) {
        return present ? "OK" : "MISSING";
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static final class MetadataStatus {
        final boolean javaEntry;
        final boolean moduleProp;
        final boolean scopeList;
        final String error;

        MetadataStatus(boolean javaEntry, boolean moduleProp, boolean scopeList, String error) {
            this.javaEntry = javaEntry;
            this.moduleProp = moduleProp;
            this.scopeList = scopeList;
            this.error = error;
        }
    }
}
