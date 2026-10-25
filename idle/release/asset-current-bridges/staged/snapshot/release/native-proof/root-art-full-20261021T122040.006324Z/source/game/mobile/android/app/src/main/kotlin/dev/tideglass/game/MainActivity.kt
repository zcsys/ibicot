package dev.tideglass.game

import android.os.SystemClock
import android.provider.Settings
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.security.KeyStore
import javax.crypto.KeyGenerator
import javax.crypto.Mac
import javax.crypto.SecretKey

class MainActivity : FlutterActivity() {
    private var ownershipClock: MethodChannel? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        ownershipClock = MethodChannel(flutterEngine.dartExecutor.binaryMessenger,
            "dev.tideglass/ownership_clock").also { channel ->
            channel.setMethodCallHandler { call, result ->
                if (call.method != "sample") {
                    result.notImplemented()
                } else {
                    try {
                        val bootCount = Settings.Global.getInt(contentResolver, Settings.Global.BOOT_COUNT)
                        check(bootCount >= 0)
                        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
                        val alias = "tideglass.ownership.clock.v1"
                        val key = if (store.containsAlias(alias)) {
                            store.getKey(alias, null) as SecretKey
                        } else {
                            KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_HMAC_SHA256,
                                "AndroidKeyStore").apply {
                                init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_SIGN)
                                    .setDigests(KeyProperties.DIGEST_SHA256).setKeySize(256).build())
                            }.generateKey()
                        }
                        // A nonexportable per-install key binds equal boot counts on
                        // different devices. Key loss/replacement changes the epoch.
                        val mac = Mac.getInstance("HmacSHA256").apply { init(key) }
                        val digest = mac.doFinal("tideglass.clock.v1:$bootCount".toByteArray(Charsets.UTF_8))
                        val epoch = Base64.encodeToString(digest,
                            Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)
                        val elapsed = SystemClock.elapsedRealtimeNanos() / 1000
                        check(elapsed >= 0)
                        result.success(mapOf("version" to 1, "elapsed_us" to elapsed,
                            "epoch_id" to "android.$epoch", "continuity_scope" to "boot"))
                    } catch (_: Exception) {
                        // No clock guess, raw boot count, key material, or exception log.
                        result.error("ownership_clock_unavailable", "Clock evidence unavailable", null)
                    }
                }
            }
        }
    }

    override fun onPause() {
        ownershipClock?.invokeMethod("invalidate", null)
        super.onPause()
    }

    override fun onResume() {
        super.onResume()
        ownershipClock?.invokeMethod("invalidate", null)
    }

    override fun cleanUpFlutterEngine(flutterEngine: FlutterEngine) {
        ownershipClock?.setMethodCallHandler(null)
        ownershipClock = null
        super.cleanUpFlutterEngine(flutterEngine)
    }
}
