interface StatusBadgeProps {
  status: string;
}

const STYLES: Record<string, { label: string; classes: string }> = {
  ready: {
    label: "Ready",
    classes: "bg-verdigris/15 text-verdigris border border-verdigris/30",
  },
  processing: {
    label: "Processing",
    classes: "bg-brass/15 text-brass border border-brass/30",
  },
  failed: {
    label: "Failed",
    classes: "bg-ember/15 text-ember border border-ember/30",
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const style = STYLES[status] ?? STYLES.processing;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style.classes}`}
    >
      {style.label}
    </span>
  );
}
