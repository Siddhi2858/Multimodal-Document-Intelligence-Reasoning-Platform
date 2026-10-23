
interface FolioTagProps {
  num: number | string;
  active?: boolean;
}

export default function FolioTag({
  num,
  active = false,
}: FolioTagProps) {
  return (
    <span
      className={`inline-flex items-center font-mono text-[11px] font-medium px-2 py-0.5 rounded border transition-colors ${
        active
          ? "border-brass text-brass bg-brass/15"
          : "border-rule text-muted bg-surface/80 hover:text-parchment"
      }`}
    >
      Page {num}
    </span>
  );
}
