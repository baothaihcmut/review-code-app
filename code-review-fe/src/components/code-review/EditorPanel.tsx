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
  const hoverDisposableRef = useRef<any>(null);
  const reviewRef = useRef<any>(null);

  const applyDecorations = () => {
  if (
    !review ||
    !review.review_items ||
    !editorRef.current ||
    !monacoRef.current
  )
    return;

  const editor = editorRef.current;
  const monaco = monacoRef.current;
  const model = editor.getModel();
  if (!model) return;

  const newDecorations: any[] = [];

  review.review_items.forEach((item: any) => {
    const className =
      item.type === "Warning" ? "line-warning" : "line-error";

    const startLine = item.line.start;
    const endLine = item.line.end;

    for (let line = startLine; line <= endLine; line++) {
      let startColumn = 0;
      let endColumn = model.getLineLastNonWhitespaceColumn(line);
      if (!endColumn || endColumn === 0) {
        endColumn = model.getLineMaxColumn(line);
      }

      newDecorations.push({
        range: new monaco.Range(line, startColumn, line, endColumn),
        options: {
          isWholeLine: false,
          className,
        },
      });
    }
  });

  decorationIds.current = editor.deltaDecorations(
    decorationIds.current,
    newDecorations
  );
};

  useEffect(() => {
    reviewRef.current = review;
    requestAnimationFrame(() => {
      applyDecorations();
    });
  }, [review]);

  const handleMount = (editor: any, monaco: any) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    if (hoverDisposableRef.current) {
      hoverDisposableRef.current.dispose();
    }

    hoverDisposableRef.current = monaco.languages.registerHoverProvider("cpp", {
      provideHover(model: any, position: any) {
        const currentReview = reviewRef.current;
        if (
          !currentReview ||
          !currentReview.review_items ||
          currentReview.review_items.length === 0
        ) {
          return null;
        }

        const item = currentReview.review_items.find((it: any) => {
          return (
            position.lineNumber >= it.line.start &&
            position.lineNumber <= it.line.end
          );
        });

        if (!item) return null;

        const startLine = item.line.start;
        const endLine = item.line.end;
        const startColumn = 1;
        const endColumn = model.getLineMaxColumn(endLine);

        return {
          range: new monaco.Range(startLine, startColumn, endLine, endColumn),
          contents: [
            { value: `**${item.type}**` },
            { value: item.issue },
            { value: `💡 _${item.fix_suggestion}_` },
          ],
        };
      },
    });
  };

  useEffect(() => {
    return () => {
      if (hoverDisposableRef.current) {
        hoverDisposableRef.current.dispose();
      }
    };
  }, []);

  return (
    <div className="p-3 border rounded-md h-full">
      <Editor
        language="cpp"
        height="100%"
        value={code}
        onChange={(v) => setCode(v ?? "")}
        onMount={handleMount}
        options={{
          renderValidationDecorations: "off",
        }}
      />
    </div>
  );
}
