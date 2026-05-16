export type ProblemDifficulty = "Easy" | "Medium" | "Hard"

export function normalizeProblemDifficulty(
  value: string | null | undefined
): ProblemDifficulty {
  if (value === "HARD" || value === "Hard") return "Hard"
  if (value === "MEDIUM" || value === "Medium") return "Medium"
  return "Easy"
}
