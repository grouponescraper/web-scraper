/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package html.strip;

/**
 *
 * @author sunitbhopal
 */




import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class HtmlStrip {
    private static final String emptyTag = "<[a-zA-Z0-9]+[^>]+>|</[a-zA-Z0-9]+>";
    private static final String commentTag = "<!--(.*?)-->";
    private static final String docTypeTag = "<![a-zA-Z0-9]+(.*?)>";

    public static void main(String[] args) throws Exception {
        File source = new File("javaword.txt");
        String text = new String(readObjectFromFile(source), "UTF-8");
        //text = "<p-if case='n=1'>TESTED_N_EQ_1</p-if>";
        text = parse(text);
        println("-------------------------------");
        println(text);
        println("-------------------------------");
    }

    private static String parse(String text) throws Exception {
        text = text.replace("\r\n", "").replace("\n", "").replace("&nbsp;", " ");
        text = replaceDocTypeTags(text);
        text = replaceCommentTags(text);
        text = replaceScriptTags(text);
        text = replaceContentTags(text);  
        text = replaceEmptyTags(text);      
        return text.replaceAll("\\s+", " ").trim();
    }
    
    private static String replaceScriptTags(String text) {
        Pattern p = Pattern.compile("(<(?<tag>(script|style))[^>]*>(?>[^<])*<\\/\\k<tag>\\s*>)", Pattern.CASE_INSENSITIVE);
        Matcher m = p.matcher(text);
        StringBuffer output = new StringBuffer();
        boolean trigger = false;
        while(m.find()){
            String find = m.group(0), tag = m.group(2);
            m.appendReplacement(output, " ");
            trigger = true;
        }
        m.appendTail(output);
        if (trigger) {
            return replaceScriptTags(output.toString());
        }
        return output.toString().replaceAll("\\s+", " ").trim();
    }

    private static String replaceDocTypeTags(String text) {
        try {
            StringBuffer output = new StringBuffer();
            Pattern pattern = Pattern.compile(docTypeTag, Pattern.MULTILINE);
            Matcher matcher = pattern.matcher(text);
            while (matcher.find()) {
                matcher.appendReplacement(output, " ");
            }
            matcher.appendTail(output);
            return output.toString().trim();
        }
        catch (Exception ex) {
        }
        return text;
    }

    private static String replaceCommentTags(String text) {
        try {
            StringBuffer output = new StringBuffer();
            Pattern pattern = Pattern.compile(commentTag, Pattern.MULTILINE);
            Matcher matcher = pattern.matcher(text);
            while (matcher.find()) {
                matcher.appendReplacement(output, " ");
            }
            matcher.appendTail(output);
            return output.toString().trim();
        }
        catch (Exception ex) {
        }
        return text;
    }

    private static String replaceContentTags(String text) {
        Pattern p = Pattern.compile("(<(?<tag>\\w+)[^>]*>(?>[^<])*<\\/\\k<tag>\\s*>)", Pattern.CASE_INSENSITIVE);
        Matcher m = p.matcher(text);
        StringBuffer output = new StringBuffer();
        boolean trigger = false;
        while(m.find()){
            String find = m.group(0), tag = m.group(2);
            if (tag != null) {
                find = find.substring(find.indexOf(">") + 1, find.length() - tag.length() - 3);
                m.appendReplacement(output, " " + Matcher.quoteReplacement(find) + " ");
            }
            else {
                m.appendReplacement(output, " ");
            }
            trigger = true;
        }
        m.appendTail(output);
        if (trigger) {
            return replaceContentTags(output.toString());
        }
        return output.toString();
    }

    private static String replaceEmptyTags(String text) {
        try {
            StringBuffer output = new StringBuffer();
            Pattern pattern = Pattern.compile(emptyTag, Pattern.MULTILINE);
            Matcher matcher = pattern.matcher(text);
            while (matcher.find()) {
                matcher.appendReplacement(output, " ");
            }
            matcher.appendTail(output);
            return output.toString().trim();
        }
        catch (Exception ex) {
        }
        return text;
    }

    private static byte[] readObjectFromFile(File source) throws Exception {
        int size = (int) source.length();
        byte[] bytes = new byte[size];
        try (BufferedInputStream inputStream = new BufferedInputStream(new FileInputStream(source))) {
            int read = inputStream.read(bytes, 0, bytes.length);
        }
        return bytes;
    }
    
    private static void println(Object o) {
        System.out.println("" + o);
    }
}
