import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../atoms/card/card';
import { Badge } from '../atoms/badge/badge';
import {
  AlertTriangle,
  CheckCircle2,
  CreditCard,
  ShieldAlert,
  Clock,
  FileSearch,
  TrendingUp,
} from 'lucide-react';
import type { CreditReport } from '../../schemas/credit-report';

interface CreditReportCardProps {
  report: CreditReport;
}

const PAYMENT_STATUS_COLORS: Record<string, string> = {
  OK: 'bg-green-500',
  '30': 'bg-yellow-500',
  '60': 'bg-orange-500',
  '90': 'bg-red-500',
  CO: 'bg-red-700',
};

function getScoreColor(score: number): string {
  if (score >= 740) return 'text-green-600';
  if (score >= 670) return 'text-yellow-600';
  if (score >= 580) return 'text-orange-600';
  return 'text-red-600';
}

function getScoreBarColor(score: number): string {
  if (score >= 740) return 'bg-green-500';
  if (score >= 670) return 'bg-yellow-500';
  if (score >= 580) return 'bg-orange-500';
  return 'bg-red-500';
}

function getScoreLabel(score: number): string {
  if (score >= 740) return 'Excellent';
  if (score >= 670) return 'Good';
  if (score >= 580) return 'Fair';
  return 'Poor';
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'medium':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    default:
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  }
}

export function CreditReportCard({ report }: CreditReportCardProps) {
  const scorePosition = ((report.credit_score - 300) / 550) * 100;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            <CardTitle className="text-lg">Credit Bureau Report</CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">
            {report.score_model}
          </Badge>
        </div>
        <CardDescription>
          Simulated credit bureau pull
          {report.pulled_at && (
            <span className="ml-1">
              ({new Date(report.pulled_at).toLocaleDateString()})
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Credit Score Gauge */}
        <div className="rounded-lg border p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium">Credit Score</span>
            <span className={`text-2xl font-bold ${getScoreColor(report.credit_score)}`}>
              {report.credit_score}
            </span>
          </div>
          <div className="mb-1 h-3 overflow-hidden rounded-full bg-gradient-to-r from-red-500 via-orange-400 via-yellow-400 to-green-500">
            <div
              className="relative h-full"
              style={{ width: `${scorePosition}%` }}
            >
              <div className="absolute right-0 top-1/2 h-5 w-1.5 -translate-y-1/2 rounded-full bg-white shadow-md" />
            </div>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>300</span>
            <span className={`font-medium ${getScoreColor(report.credit_score)}`}>
              {getScoreLabel(report.credit_score)}
            </span>
            <span>850</span>
          </div>
        </div>

        {/* Score Factors */}
        {report.score_factors.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              Score Factors
            </h4>
            <div className="space-y-1">
              {report.score_factors.map((factor, i) => (
                <p key={i} className="text-xs text-muted-foreground">
                  {factor}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Summary Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border p-2.5 text-center">
            <p className="text-xs text-muted-foreground">Utilization</p>
            <p className={`text-lg font-bold ${
              (report.credit_utilization ?? 0) <= 30
                ? 'text-green-600'
                : (report.credit_utilization ?? 0) <= 50
                  ? 'text-yellow-600'
                  : 'text-red-600'
            }`}>
              {report.credit_utilization != null ? `${report.credit_utilization.toFixed(0)}%` : 'N/A'}
            </p>
          </div>
          <div className="rounded-lg border p-2.5 text-center">
            <p className="text-xs text-muted-foreground">On-Time</p>
            <p className={`text-lg font-bold ${
              (report.on_time_payments_pct ?? 0) >= 97
                ? 'text-green-600'
                : (report.on_time_payments_pct ?? 0) >= 90
                  ? 'text-yellow-600'
                  : 'text-red-600'
            }`}>
              {report.on_time_payments_pct != null
                ? `${report.on_time_payments_pct.toFixed(1)}%`
                : 'N/A'}
            </p>
          </div>
          <div className="rounded-lg border p-2.5 text-center">
            <p className="text-xs text-muted-foreground">Accounts</p>
            <p className="text-lg font-bold">
              {report.open_accounts}/{report.total_accounts}
            </p>
            <p className="text-[10px] text-muted-foreground">open</p>
          </div>
          <div className="rounded-lg border p-2.5 text-center">
            <p className="text-xs text-muted-foreground">Oldest Acct</p>
            <p className="text-lg font-bold">
              {report.oldest_account_months != null
                ? `${Math.floor(report.oldest_account_months / 12)}y`
                : 'N/A'}
            </p>
          </div>
        </div>

        {/* Late Payments Summary */}
        {(report.late_payments_30d > 0 || report.late_payments_60d > 0 || report.late_payments_90d > 0) && (
          <div className="rounded-lg border border-orange-200 bg-orange-50 p-3">
            <h4 className="mb-1 text-sm font-medium text-orange-800">Late Payments</h4>
            <div className="flex gap-4 text-xs">
              {report.late_payments_30d > 0 && (
                <span className="text-orange-700">30-day: {report.late_payments_30d}</span>
              )}
              {report.late_payments_60d > 0 && (
                <span className="text-orange-700">60-day: {report.late_payments_60d}</span>
              )}
              {report.late_payments_90d > 0 && (
                <span className="text-red-700">90+ day: {report.late_payments_90d}</span>
              )}
            </div>
          </div>
        )}

        {/* Tradelines */}
        {report.tradelines.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
              <CreditCard className="h-4 w-4" />
              Tradelines ({report.tradelines.length})
            </h4>
            <div className="space-y-3">
              {report.tradelines.map((tl, i) => (
                <div key={i} className="rounded-lg border p-3">
                  <div className="mb-1 flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium">{tl.creditor}</span>
                      <span className="ml-2 text-xs text-muted-foreground capitalize">
                        {tl.account_type.replace('_', ' ')}
                      </span>
                    </div>
                    <Badge variant={tl.status === 'open' ? 'default' : 'secondary'} className="text-xs">
                      {tl.status}
                    </Badge>
                  </div>
                  <div className="mb-2 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                    {tl.credit_limit != null && (
                      <div>Limit: ${tl.credit_limit.toLocaleString()}</div>
                    )}
                    <div>Balance: ${tl.current_balance.toLocaleString()}</div>
                    <div>Payment: ${tl.monthly_payment.toLocaleString()}/mo</div>
                  </div>
                  {/* Payment History Heatmap */}
                  {tl.payment_history_24m.length > 0 && (
                    <div>
                      <p className="mb-1 text-[10px] text-muted-foreground">
                        24-month payment history (most recent left)
                      </p>
                      <div className="flex gap-0.5">
                        {tl.payment_history_24m.map((status, j) => (
                          <div
                            key={j}
                            className={`h-2.5 flex-1 rounded-sm ${PAYMENT_STATUS_COLORS[status] ?? 'bg-gray-300'}`}
                            title={`Month ${j + 1}: ${status}`}
                          />
                        ))}
                      </div>
                      <div className="mt-0.5 flex justify-between text-[9px] text-muted-foreground">
                        <span>Recent</span>
                        <span>24mo ago</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Public Records */}
        {report.public_records.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-red-700">
              <AlertTriangle className="h-4 w-4" />
              Public Records
            </h4>
            <div className="space-y-2">
              {report.public_records.map((pr, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 p-3 text-sm">
                  <div>
                    <span className="font-medium capitalize text-red-800">
                      {pr.record_type}
                    </span>
                    <span className="ml-2 text-xs text-red-600">
                      Filed: {new Date(pr.filed_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline" className="text-xs capitalize">
                      {pr.status}
                    </Badge>
                    {pr.amount != null && (
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        ${pr.amount.toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Inquiries */}
        {report.inquiries.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
              <FileSearch className="h-4 w-4" />
              Recent Inquiries ({report.inquiries.length})
            </h4>
            <div className="space-y-1">
              {report.inquiries.map((inq, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span>{inq.creditor}</span>
                    <Badge variant="secondary" className="text-[10px] px-1 py-0 capitalize">
                      {inq.inquiry_type}
                    </Badge>
                  </div>
                  <span className="text-muted-foreground">
                    {new Date(inq.date).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Collections */}
        {report.collections.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-orange-700">
              <AlertTriangle className="h-4 w-4" />
              Collections ({report.collections.length})
            </h4>
            <div className="space-y-2">
              {report.collections.map((col, i) => (
                <div key={i} className="rounded-lg border border-orange-200 bg-orange-50 p-2 text-xs">
                  <div className="flex justify-between">
                    <span className="font-medium">{col.agency}</span>
                    <Badge variant="outline" className="text-[10px] capitalize">
                      {col.status}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground">
                    Original: {col.original_creditor} &middot; ${col.amount.toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fraud Indicators */}
        <div>
          <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
            <ShieldAlert className="h-4 w-4" />
            Fraud Risk
            <Badge
              variant="outline"
              className={`ml-1 text-xs ${
                report.fraud_score >= 40
                  ? 'border-red-300 text-red-700'
                  : report.fraud_score >= 20
                    ? 'border-orange-300 text-orange-700'
                    : 'border-green-300 text-green-700'
              }`}
            >
              {report.fraud_score}/100
            </Badge>
          </h4>
          {report.fraud_alerts.length > 0 ? (
            <div className="space-y-1.5">
              {report.fraud_alerts.map((alert, i) => (
                <div
                  key={i}
                  className={`rounded-md border px-3 py-2 text-xs ${getSeverityColor(alert.severity)}`}
                >
                  <div className="flex items-center gap-1.5">
                    {alert.severity === 'high' ? (
                      <AlertTriangle className="h-3 w-3 shrink-0" />
                    ) : (
                      <CheckCircle2 className="h-3 w-3 shrink-0" />
                    )}
                    <span className="font-medium capitalize">
                      {alert.alert_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[11px]">{alert.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="flex items-center gap-1 text-xs text-green-700">
              <CheckCircle2 className="h-3 w-3" />
              No fraud indicators detected
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
