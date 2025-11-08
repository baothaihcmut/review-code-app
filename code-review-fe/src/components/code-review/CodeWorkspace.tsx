import ProblemPanel from "./ProblemPanel";
import EditorPanel from "./EditorPanel";
import ReviewPanel from "./ReviewPanel";
import TestCasePanel from "./TestCasePanel";

export default function CodeWorkspace() {
  return (
    <div className="flex flex-col lg:flex-row gap-4 h-full w-full p-4">
      <div className="flex flex-col gap-4 flex-1 lg:flex-3 min-h-0">
        <ProblemPanel />
        <EditorPanel />
        <TestCasePanel />
      </div>
      <div className="flex flex-col flex-1 lg:flex-1 min-h-0">
        <ReviewPanel/>
      </div>
    </div>
  );
}
