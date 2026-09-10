# libxposed API 102 recommended module-entry rules. These are kept even while
# minification is disabled so enabling R8 later cannot strip or desynchronize
# the modern META-INF/xposed Java entry.
-dontwarn io.github.libxposed.annotation.**
-adaptresourcefilecontents META-INF/xposed/java_init.list
-keep,allowoptimization,allowobfuscation public class * extends io.github.libxposed.api.XposedModule {
    public <init>();
}
