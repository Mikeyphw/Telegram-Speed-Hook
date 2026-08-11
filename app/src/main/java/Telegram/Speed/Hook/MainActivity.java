package Telegram.Speed.Hook;

import android.app.Activity;
import android.os.Bundle;
import android.text.method.LinkMovementMethod;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
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

        TextView body = new TextView(this);
        body.setText(
                "LSPosed/Xposed module loaded by Telegram or Nullgram.\n\n" +
                "Supported scopes:\n" +
                "• org.telegram.messenger\n" +
                "• top.qwq2333.nullgram\n\n" +
                "After installing, enable the module in LSPosed, select the target app, " +
                "force-stop Telegram/Nullgram, and reopen it.\n\n" +
                "Check logs with:\n" +
                "adb logcat -v time | grep TgSpeedHook"
        );
        body.setTextSize(15);
        body.setMovementMethod(LinkMovementMethod.getInstance());

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

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
