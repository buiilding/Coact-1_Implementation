
import { CurrentTaskDisplay } from "./CurrentTaskDisplay";
import { ScreenshotViewer } from "./ScreenshotViewer";
import { PreviousScreenshot } from "./PreviousScreenshot";
import { AgentTree } from "./AgentTree";
import { FunctionCallLog } from "./FunctionCallLog";
import { OCRContentList } from "./OCRContentList";
import { GroundingModelPanel } from "./GroundingModelPanel";

export const Dashboard = () => {
  return (
    <div className="h-screen w-full bg-background overflow-hidden">
      {/* Main Grid Layout */}
      <div className="h-screen grid grid-cols-12 grid-rows-6 gap-2 p-2">
        {/* Left Column - 2 units wide */}
        <div className="col-span-2 row-span-2">
          <CurrentTaskDisplay />
        </div>

        {/* Center Column - 8 units wide, full height */}
        <div className="col-span-8 row-span-6">
          <ScreenshotViewer />
        </div>

        {/* Right Column - 2 units wide */}
        <div className="col-span-2 row-span-2">
          <PreviousScreenshot />
        </div>

        {/* Agent Tree - Left, rows 3-4 */}
        <div className="col-span-2 row-span-2">
          <AgentTree />
        </div>

        {/* OCR Content - Right, rows 3-4 */}
        <div className="col-span-2 row-span-2">
          <OCRContentList />
        </div>

        {/* Function Log - Left, rows 5-6 */}
        <div className="col-span-2 row-span-2">
          <FunctionCallLog />
        </div>

        {/* Grounding Model - Right, rows 5-6 */}
        <div className="col-span-2 row-span-2">
          <GroundingModelPanel />
        </div>
      </div>

    </div>
  );
};