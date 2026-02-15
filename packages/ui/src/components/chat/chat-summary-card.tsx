import { Card, CardContent, CardHeader, CardTitle } from '../atoms/card/card';

interface ChatSummaryCardProps {
  summary: Record<string, unknown>;
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return value.toLocaleString();
  return String(value);
}

export function ChatSummaryCard({ summary }: ChatSummaryCardProps) {
  const sections = Object.entries(summary).filter(
    ([, value]) => value !== null && value !== undefined,
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Application Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {sections.map(([key, value]) => {
          if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
            const nested = value as Record<string, unknown>;
            return (
              <div key={key} className="space-y-1">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {formatLabel(key)}
                </h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm">
                  {Object.entries(nested)
                    .filter(([, v]) => v !== null && v !== undefined)
                    .map(([k, v]) => (
                      <div key={k} className="contents">
                        <span className="text-muted-foreground">{formatLabel(k)}</span>
                        <span>{renderValue(v)}</span>
                      </div>
                    ))}
                </div>
              </div>
            );
          }

          return (
            <div key={key} className="flex justify-between text-sm">
              <span className="text-muted-foreground">{formatLabel(key)}</span>
              <span className="font-medium">{renderValue(value)}</span>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
