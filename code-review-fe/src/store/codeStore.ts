/* eslint-disable */
import { create } from "zustand";

type ReviewItem = {
  line: number;
  message: string;
  suggestion?: string;
  type: "error" | "warning";
};

type CodeStore = {
  code: string;
  setCode: (val: string) => void;
  review: {
    errors: ReviewItem[];
    warnings: ReviewItem[];
    improvements: string[];
    understanding: string;
  } | null;
  setReview: (val: any) => void;
};

export const useCodeStore = create<CodeStore>((set) => ({
  code: `int len = strlen(str);
  int j = 0;
  bool inSpace = false;
  int i = 0;

  while (i < len && str[i] == ' ') i++;

  for (; i < len; i++) {
      if (str[i] != ' ') {
          outstr[j++] = str[i];
          inSpace = false;
      } else {
          if (!inSpace) {
              outstr[j++] = ' ';
              inSpace = true;
          }
      }
  }

  if (j > 0 && outstr[j-1] == ' ') j--;

  outstr[j] = '\\0';`,
  setCode: (val) => set({ code: val }),
  review: null,
  setReview: (val) => set({ review: val }),
}));
