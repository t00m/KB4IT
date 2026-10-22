import { EditorState, Compartment } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLine, drawSelection } from "@codemirror/view";
import { history, historyKeymap, defaultKeymap, indentWithTab, indentMore, indentLess, undo, redo } from "@codemirror/commands";
import { syntaxTree, HighlightStyle, syntaxHighlighting, indentUnit } from "@codemirror/language";
import { searchKeymap } from "@codemirror/search";
import { closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap } from "@codemirror/autocomplete";
import { linter, lintGutter, forceLinting } from "@codemirror/lint";
import { markdown, markdownKeymap } from "@codemirror/lang-markdown";
import { yamlFrontmatter } from "@codemirror/lang-yaml";
import { tags } from "@lezer/highlight";

export const cm = {
    EditorView, EditorState, Compartment, keymap, lineNumbers, highlightActiveLine, drawSelection,
    history, historyKeymap, defaultKeymap, indentWithTab, indentMore, indentLess, undo, redo,
    searchKeymap, closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap,
    linter, lintGutter, forceLinting, syntaxTree, HighlightStyle, syntaxHighlighting, indentUnit, tags,
    markdown, markdownKeymap, yamlFrontmatter,
};
