import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface RiskBadgeProps {
  score: number | null | undefined;
}

export function RiskBadge({ score }: RiskBadgeProps) {
  if (score === null || score === undefined) {
    return <Badge variant="secondary">—</Badge>;
  }

  let label: string;
  let className: string;

  if (score <= 30) {
    label = `${score}`;
    className = "bg-green-500/10 text-green-600 border-green-500/20";
  } else if (score <= 55) {
    label = `${score}`;
    className = "bg-yellow-500/10 text-yellow-600 border-yellow-500/20";
  } else if (score <= 80) {
    label = `${score}`;
    className = "bg-orange-500/10 text-orange-600 border-orange-500/20";
  } else {
    label = `${score}`;
    className = "bg-red-500/10 text-red-600 border-red-500/20";
  }

  return (
    <Badge variant="outline" className={cn("font-mono text-xs", className)}>
      {label}
    </Badge>
  );
}
