/* eslint-disable */
"use client";
import { Loader2 } from "lucide-react";

import { useCodeStore } from "@/store/codeStore";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";

export default function ReviewPanel() {
  const { code, review, setReview } = useCodeStore() as any;
  const [isLoading, setIsLoading] = useState(false);

  const handleReview = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("⁦http://localhost:8080/api/review⁩", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assignment: { content: "This is test version", language: "cpp" },
          submission: { code },
        }),
      });

      const data = await res.json();
      setReview(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full h-full p-4 flex flex-col">
      <div className="flex justify-between items-center">
        <h2 className="font-semibold text-lg">Phản hồi từ AI</h2>
        <Button onClick={handleReview} disabled={isLoading}>
          {isLoading ? (
            <Loader2 className="animate-spin" />
          ) : (
            "Review Code"
          )}
        </Button>
      </div>

      <Separator className="my-3" />

      <ScrollArea className="flex-1 text-sm space-y-3">
        {review?.review_items?.map((item: any, i: number) => (
          <div key={i} className="border p-2 rounded">
            <div className="font-semibold">🔍 {item.type}</div>
            <div className="text-gray-800">{item.issue}</div>
            <div className="text-gray-500 text-xs">
              Gợi ý: {item.fix_suggestion}
            </div>
          </div>
        ))}
      </ScrollArea>
    </Card>
  );
}