"""Face buttons on an AYN handheld (Settings.faceButtons / Settings.device with games/totk/tests/settings/OdinButtonsTest.java): settings.env says
TOTK_FACE_BUTTONS=position when the device is AYN's and its system Controller style is Xbox, and is otherwise byte for byte what the menu's choice gave before;
SettingsStore hands the device over at every write. The runtime and the two dialogs that read TOTK_FACE_BUTTONS are untouched, so they stay in step.
Each mutation of Settings.java must make the JVM test fail; one that cannot be applied exactly once is a fault of this test, reported as such."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOTK = ROOT / 'games/totk'
SETUP = TOTK / 'android/java/com/aure/totk/setup'
SOURCE = SETUP / 'Settings.java'
TEST = TOTK / 'tests/settings/OdinButtonsTest.java'

MUTATIONS = [
    ('if ("xbox".equals(buttons)) return "position";', 'if ("xbox".equals(buttons)) return "label";', 'the menu\'s Xbox choice is lost'),
    ('return aynXboxStyle ? "position" : "label";', 'return aynXboxStyle ? "label" : "label";', 'the Xbox style is ignored'),
    ('return aynXboxStyle ? "position" : "label";', 'return aynXboxStyle ? "label" : "position";', 'inverted'),
    ('AYN.equals(maker == null ? "" : maker.trim()) && AYN_STYLE_XBOX', '(maker == null || maker != null) && AYN_STYLE_XBOX', 'any maker'),
    ('&& AYN_STYLE_XBOX.equals(style == null ? "" : style.trim());', '&& (style == null || style != null);', 'any style'),
    ('AYN.equals(maker == null ? "" : maker.trim()) && AYN_STYLE_XBOX', 'AYN.equals(maker == null ? "" : maker.trim()) || AYN_STYLE_XBOX', 'maker or style'),
    ('AYN.equals(maker == null ? "" : maker.trim())', 'AYN.equalsIgnoreCase(maker == null ? "" : maker.trim())', 'the maker is matched loosely'),
    ('AYN.equals(maker == null ? "" : maker.trim())', 'AYN.equals(maker == null ? "" : maker)', 'the maker is not trimmed'),
    ('AYN_STYLE_XBOX.equals(style == null ? "" : style.trim())', 'AYN_STYLE_XBOX.equals(style == null ? "" : style)', 'the style is not trimmed'),
    ('AYN_STYLE_XBOX = "1"', 'AYN_STYLE_XBOX = "0"', 'the default style is taken for Xbox'),
    ('AYN = "AYN"', 'AYN = "AY"', 'another maker'),
    ('AYN_STYLE_PROPERTY = "persist.sys.gamepad.type"', 'AYN_STYLE_PROPERTY = "persist.sys.gamepad"', 'another property'),
    ('faceButtons(get("buttons"), deviceMaker, controllerStyle)', 'faceButtons(get("buttons"), "", "")', 'settings.env ignores the device'),
    ('faceButtons(get("buttons"), deviceMaker, controllerStyle)', 'faceButtons(get("buttons"), controllerStyle, deviceMaker)', 'maker and style swapped'),
    ('        controllerStyle = style == null ? "" : style;\n', '', 'the style is not kept'),
    ('        deviceMaker = maker == null ? "" : maker;\n', '', 'the maker is not kept'),
]
NEUTRAL = ('/** TOTK_FACE_BUTTONS for the menu\'s Button layout on this device:', '/** TOTK_FACE_BUTTONS for the menu\'s Button layout on the device:')


def swap(text, needle, replacement):
    if text.count(needle) != 1:
        raise RuntimeError('SETUP-ERROR: needle occurs %d times: %r' % (text.count(needle), needle))
    changed = text.replace(needle, replacement)
    if changed == text:
        raise RuntimeError('SETUP-ERROR: the mutation changes nothing: %r' % needle)
    return changed


def jvm(source_text):
    """(stage, returncode, output) of compiling Settings (as given) with the test and running it."""
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / 'Settings.java'
        src.write_text(source_text, encoding='utf-8')
        c = subprocess.run(['javac', '--release', '17', '-encoding', 'UTF-8', '-d', d, str(src), str(TEST)], capture_output=True, text=True)
        if c.returncode:
            return 'javac', c.returncode, c.stderr
        r = subprocess.run(['java', '-cp', d, 'com.aure.totk.setup.OdinButtonsTest'], capture_output=True, text=True)
        return 'java', r.returncode, r.stdout + r.stderr


class Wiring(unittest.TestCase):
    def test_store_hands_over_the_device_at_every_write(self):
        store = (SETUP / 'SettingsStore.java').read_text(encoding='utf-8')
        write = store[store.index('static String writeEnv(Context context, Settings settings) {'):]
        self.assertLess(write.index('settings.device(Build.MANUFACTURER, controllerStyle());'), write.index('Settings.writeAtomic('))
        self.assertIn('.invoke(null, Settings.AYN_STYLE_PROPERTY, "")', store)
        self.assertEqual(store.count('settings.env('), 1, 'one place writes settings.env')

    def test_readers_of_the_setting_are_untouched(self):
        frontend = (TOTK / 'runtime/frontend_android.c').read_text(encoding='utf-8')
        self.assertIn('by_label = !(e && !strcmp(e, "position"));', frontend)   # the game reads the file's verdict


@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'no JDK')
class OdinButtonsJvm(unittest.TestCase):
    def test_jvm_and_mutations(self):
        good = SOURCE.read_text(encoding='utf-8')
        stage, rc, out = jvm(good)
        self.assertEqual((stage, rc, out.strip()), ('java', 0, 'ok'), out)
        survived = []
        for needle, replacement, what in MUTATIONS:
            stage, rc, out = jvm(swap(good, needle, replacement))
            if stage == 'javac':
                raise RuntimeError('SETUP-ERROR: mutant %r does not compile:\n%s' % (what, out))
            if rc == 0:
                survived.append(what)
        self.assertEqual(survived, [], 'mutations the JVM test did not catch')
        stage, rc, out = jvm(swap(good, *NEUTRAL))
        self.assertEqual((stage, rc, out.strip()), ('java', 0, 'ok'), 'a comment-only change must still pass: ' + out)


if __name__ == '__main__':
    unittest.main()
