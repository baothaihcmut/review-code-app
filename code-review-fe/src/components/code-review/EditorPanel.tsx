/* eslint-disable */
"use client";
import { useRef, useEffect } from "react";
import { useCodeStore } from "@/store/codeStore";
import Editor from "@monaco-editor/react";

export default function EditorPanel() {
  const { code, setCode, review } = useCodeStore() as any;
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const decorationIds = useRef<string[]>([]);

  console.log('review', review)

  const applyDecorations = () => {
    if (!review || !review.review_items || !editorRef.current || !monacoRef.current) return;

    const editor = editorRef.current;
    const monaco = monacoRef.current;

    const newDecorations = review.review_items.map((item: any) => ({
      range: new monaco.Range(item.line.start, 1, item.line.end, 1),
      options: {
        isWholeLine: true,
        inlineClassName: item.type == "Correctness" ? "line-warning" : "line-error",
        hoverMessage: {
          value: `**${item.type}**\n\n${item.issue}\n\n💡 *${item.fix_suggestion}*`,
        },
      },
    }));

    decorationIds.current = editor.deltaDecorations(
      decorationIds.current,
      newDecorations
    );
  };

  useEffect(() => {
    requestAnimationFrame(applyDecorations);
  }, [review]);

  return (
    <div className="p-3 border rounded-md min-h-[400px]">
      <Editor
        language="cpp"
        height="100%"
        value={code}
        onChange={(v) => setCode(v ?? "")}
        onMount={(editor, monaco) => {
          editorRef.current = editor;
          monacoRef.current = monaco;
        }}
        options={{ renderValidationDecorations: "off" }}
      />
    </div>
  );
}