package com.aure.totk.setup;

/** Settings.faceButtons and Settings.device on the JVM (tests/test_android_odin_buttons.py): the face-button layout on an AYN handheld follows its
 * Controller style. Prints "ok" or throws. */
public final class OdinButtonsTest {
    private static void check(boolean c, String what) { if (!c) throw new AssertionError(what); }
    private static String face(String env) {
        for (String line : env.split("\n")) if (line.startsWith("TOTK_FACE_BUTTONS=")) return line.substring("TOTK_FACE_BUTTONS=".length());
        throw new AssertionError("no TOTK_FACE_BUTTONS line");
    }

    public static void main(String[] args) {
        check(Settings.AYN.equals("AYN") && Settings.AYN_STYLE_PROPERTY.equals("persist.sys.gamepad.type") && Settings.AYN_STYLE_XBOX.equals("1"),
              "the maker, the property and its Xbox value");

        // the menu's choice alone, off an AYN device or in the default style
        for (String maker : new String[] {"AYN", "samsung", "", null})
            for (String style : new String[] {"0", "", null, "2", "10", "01", "xbox", "1 1"}) {
                check(Settings.faceButtons("nintendo", maker, style).equals("label"), "Nintendo stays by label: " + maker + " / " + style);
                check(Settings.faceButtons("xbox", maker, style).equals("position"), "Xbox stays by position: " + maker + " / " + style);
            }
        // an AYN device in the Xbox style: by position whatever the menu says
        check(Settings.faceButtons("nintendo", "AYN", "1").equals("position"), "AYN, Xbox style, menu Nintendo");
        check(Settings.faceButtons("xbox", "AYN", "1").equals("position"), "AYN, Xbox style, menu Xbox");
        check(Settings.faceButtons("nintendo", " AYN ", " 1\n").equals("position"), "both values are trimmed");
        // the style of another maker's device means nothing
        for (String maker : new String[] {"samsung", "ayn", "AYNX", "AY", "", null})
            check(Settings.faceButtons("nintendo", maker, "1").equals("label"), "not AYN: " + maker);
        check(Settings.faceButtons(null, "samsung", "0").equals("label") && Settings.faceButtons("", null, null).equals("label"), "no choice reads as Nintendo");

        // through settings.env: unchanged until the device is given, and then only on AYN in the Xbox style
        Settings s = new Settings(null, "QCS8550");
        String before = s.env("en-GB");
        check(face(before).equals("label"), "the default file");
        check(s.device("AYN", "0").env("en-GB").equals(before), "AYN in its default style: the same bytes");
        check(s.device("samsung", "1").env("en-GB").equals(before), "another maker: the same bytes");
        check(s.device(null, null).env("en-GB").equals(before), "unknown device: the same bytes");
        String xbox = s.device("AYN", "1").env("en-GB");
        check(face(xbox).equals("position"), "AYN in the Xbox style");
        check(xbox.equals(before.replace("TOTK_FACE_BUTTONS=label\n", "TOTK_FACE_BUTTONS=position\n")), "only that line differs");
        check(face(s.device("AYN", "0").env("en-GB")).equals("label"), "back in the default style");
        s.set("buttons", "xbox");
        check(face(s.device("AYN", "0").env("en-GB")).equals("position") && face(s.device("", "").env("en-GB")).equals("position"), "the menu's Xbox choice");
        System.out.println("ok");
    }
}
