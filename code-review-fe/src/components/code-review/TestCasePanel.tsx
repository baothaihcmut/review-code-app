/* eslint-disable */
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useCodeStore } from "@/store/codeStore";

export default function TestCasePanel() {
  const { code } = useCodeStore() as any;
  const [results, setResults] = useState<any[] | null>(null);

  const handleRun = async () => {
    try {
      const res = await fetch("http://localhost:8080/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assignment: {
            content: "This is test version",
            language: "cpp",
          },
          submission: { code },
          testcase: [
            { name: "Testcase 01", input: "   Hello   world   ", expect: "Hello world" },
            { name: "Testcase 02", input: "  OpenAI    GPT    5  ", expect: "OpenAI GPT 5" },
            { name: "Testcase 03", input: "NoExtraSpace", expect: "NoExtraSpace" }
          ]
        })
      });

      const data = await res.json();
      setResults(data.testcaseResults ?? []);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-3 border rounded-md min-h-40">
      <h2 className="font-semibold mb-2">Test Case</h2>
      <Button onClick={handleRun}>Run</Button>

      {results && (
        <div className="mt-3 space-y-2 text-sm">
          {results.map((tc, i) => (
            <div key={i} className={tc.status === "PASSED" ? "text-green-600" : "text-red-600"}>
              {tc.status === "PASSED" ? "✅" : "❌"} {tc.name}  
              <br/>
              <span className="text-xs text-gray-600">Expect: {tc.expect}</span><br/>
              <span className="text-xs text-gray-600">Actual: {tc.actual}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
