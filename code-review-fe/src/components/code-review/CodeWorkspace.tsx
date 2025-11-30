import ProblemPanel from "./ProblemPanel";
import EditorPanel from "./EditorPanel";
import ReviewPanel from "./ReviewPanel";
import TestCasePanel from "./TestCasePanel";

export default function CodeWorkspace() {
  return (
    <div className="flex flex-col lg:flex-row gap-4 h-screen w-full p-4">
      <div className="flex flex-col flex-1 min-h-0 h-full">
        <ProblemPanel />
      </div>
      <div className="flex flex-col gap-2 flex-1 lg:flex-3 min-h-0 max-w-[650px]">
        <div className="flex-6 min-h-0">
          <EditorPanel />
        </div>
        <div className="flex-4 min-h-0">
          <TestCasePanel />
        </div>

      </div>
      <div className="flex flex-col flex-1 lg:flex-1 min-h-0">
        <ReviewPanel />
      </div>
    </div>
  );
}