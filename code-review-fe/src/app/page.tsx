import Link from "next/link";
import { AuroraBackground } from "@/components/ui/shadcn-io/aurora-background";

export default function Page() {
  return (
    <AuroraBackground>
      <div className="relative flex flex-col gap-4 items-center justify-center px-4">
        <div className="text-3xl md:text-7xl font-bold dark:text-white text-center">
          Background lights are cool you know.
        </div>
        <div className="font-extralight text-base md:text-4xl dark:text-neutral-200 py-4">
          And this, is chemical burn.
        </div>
        <Link
          href="/code-review"
          className="bg-black dark:bg-white rounded-full w-fit text-white dark:text-black px-4 py-2"
        >
          Review Code
        </Link>
      </div>
    </AuroraBackground>
  );
}
