/* eslint-disable */
"use client";
import { Loader2 } from "lucide-react";

import { useCodeStore } from "@/store/codeStore";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";
import { MessageResponse } from "../ai-elements/message";
import { Skeleton } from "../ui/skeleton";

export default function ReviewPanel() {
  const { code, review, setReview } = useCodeStore() as any;
  const [isLoading, setIsLoading] = useState(false);

  const handleReview = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8080/api/review", {
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
          {isLoading ? <Loader2 className="animate-spin" /> : "Review Code"}
        </Button>
      </div>

      <Separator className="my-3" />

      <div className="flex-1 min-h-0">
        <ScrollArea className="h-full">
          <div className="space-y-3 text-sm p-1">
            {isLoading ? (
              <>
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
                <Skeleton className="h-4 w-2/3" />
              </>
            ) : (
              <MessageResponse>{review?.summary}</MessageResponse>
            )}
          </div>
        </ScrollArea>
      </div>
    </Card>
  );
}
