import { createFileRoute, Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useLoanProduct, useEligibilityCheck } from '../../hooks/loans';
import { Badge } from '../../components/atoms/badge/badge';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { ArrowLeft, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/loans/$loanId' as any)({
  component: LoanDetailPage,
});

function LoanDetailPage() {
  const { loanId } = Route.useParams();
  const { data: loan, isLoading } = useLoanProduct(loanId);
  const eligibilityCheck = useEligibilityCheck(loanId);

  const [formData, setFormData] = useState({
    annual_income: '',
    monthly_debts: '',
    credit_score_range: '720-759',
    down_payment_amount: '',
    property_value: '',
    citizenship_status: 'citizen',
  });

  const handleCheckEligibility = () => {
    eligibilityCheck.mutate({
      annual_income: Number(formData.annual_income),
      monthly_debts: Number(formData.monthly_debts),
      credit_score_range: formData.credit_score_range,
      down_payment_amount: Number(formData.down_payment_amount),
      property_value: Number(formData.property_value),
      citizenship_status: formData.citizenship_status,
    });
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl p-4 sm:p-6 lg:p-8">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!loan) {
    return (
      <div className="mx-auto max-w-4xl p-4 sm:p-6 lg:p-8">
        <p className="text-muted-foreground">Loan product not found.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-6 lg:p-8">
      <Link
        to="/loans"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Loan Products
      </Link>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="mb-2 flex gap-2">
            <Badge variant="secondary">{loan.type}</Badge>
            <Badge variant="outline">{loan.rate_type}</Badge>
          </div>
          <h1 className="text-2xl font-bold">{loan.name}</h1>
          <p className="mt-1 text-muted-foreground">{loan.description}</p>
        </div>
        <Link to="/applications/new" search={{ loanProductId: loan.id }}>
          <Button>Apply Now</Button>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Loan Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Loan Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Term</span>
              <span className="font-medium">{loan.term_years} years</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Rate Type</span>
              <span className="font-medium">{loan.rate_type}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Min. Down Payment</span>
              <span className="font-medium">
                {loan.min_down_payment_pct}%
              </span>
            </div>
            {loan.min_credit_score && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Min. Credit Score
                </span>
                <span className="font-medium">{loan.min_credit_score}</span>
              </div>
            )}
            {loan.max_dti_ratio && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Max. DTI Ratio</span>
                <span className="font-medium">{loan.max_dti_ratio}%</span>
              </div>
            )}
            {loan.max_loan_amount && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Max. Loan Amount</span>
                <span className="font-medium">
                  ${loan.max_loan_amount.toLocaleString()}
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Requirements & Features */}
        <div className="space-y-6">
          {loan.eligibility_requirements.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Eligibility Requirements
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {loan.eligibility_requirements.map((req, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                      {req}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {loan.features.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Features</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {loan.features.map((feature, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Eligibility Check */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">
            Quick Eligibility Pre-Check
          </CardTitle>
          <CardDescription>
            Enter your information below to get a quick estimate of your
            eligibility for this loan product.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm font-medium">
                Annual Income ($)
              </label>
              <input
                type="number"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="85000"
                value={formData.annual_income}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    annual_income: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Monthly Debts ($)
              </label>
              <input
                type="number"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="1200"
                value={formData.monthly_debts}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    monthly_debts: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Credit Score Range
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={formData.credit_score_range}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    credit_score_range: e.target.value,
                  }))
                }
              >
                <option value="760-850">760-850 (Excellent)</option>
                <option value="720-759">720-759 (Very Good)</option>
                <option value="680-719">680-719 (Good)</option>
                <option value="640-679">640-679 (Fair)</option>
                <option value="580-639">580-639 (Below Average)</option>
                <option value="300-579">300-579 (Poor)</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Property Value ($)
              </label>
              <input
                type="number"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="350000"
                value={formData.property_value}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    property_value: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Down Payment ($)
              </label>
              <input
                type="number"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="25000"
                value={formData.down_payment_amount}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    down_payment_amount: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Citizenship Status
              </label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={formData.citizenship_status}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    citizenship_status: e.target.value,
                  }))
                }
              >
                <option value="citizen">US Citizen</option>
                <option value="permanent_resident">Permanent Resident</option>
                <option value="visa_holder">Visa Holder</option>
                <option value="non_resident">Non-Resident</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <Button
              onClick={handleCheckEligibility}
              disabled={
                eligibilityCheck.isPending ||
                !formData.annual_income ||
                !formData.property_value ||
                !formData.down_payment_amount
              }
            >
              {eligibilityCheck.isPending
                ? 'Checking...'
                : 'Check Eligibility'}
            </Button>
          </div>

          {/* Results */}
          {eligibilityCheck.data && (
            <div className="mt-6 rounded-lg border p-4">
              <div className="mb-3 flex items-center gap-2">
                {eligibilityCheck.data.eligible ? (
                  <>
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    <span className="font-medium text-green-700">
                      You may be eligible for this loan
                    </span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    <span className="font-medium text-yellow-700">
                      You may not currently meet eligibility requirements
                    </span>
                  </>
                )}
              </div>

              {eligibilityCheck.data.estimated_rate && (
                <div className="mb-2 text-sm">
                  <span className="text-muted-foreground">
                    Estimated Rate:{' '}
                  </span>
                  <span className="font-medium">
                    {eligibilityCheck.data.estimated_rate}
                  </span>
                </div>
              )}

              {eligibilityCheck.data.estimated_monthly_payment && (
                <div className="mb-2 text-sm">
                  <span className="text-muted-foreground">
                    Estimated Monthly Payment:{' '}
                  </span>
                  <span className="font-medium">
                    $
                    {eligibilityCheck.data.estimated_monthly_payment.toLocaleString(
                      undefined,
                      { maximumFractionDigits: 0 },
                    )}
                  </span>
                </div>
              )}

              {eligibilityCheck.data.warnings.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">
                    Warnings
                  </p>
                  <ul className="space-y-1">
                    {eligibilityCheck.data.warnings.map((w, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-yellow-700"
                      >
                        <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {eligibilityCheck.data.suggestions.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">
                    Suggestions
                  </p>
                  <ul className="space-y-1">
                    {eligibilityCheck.data.suggestions.map((s, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-blue-700"
                      >
                        <Info className="mt-0.5 h-3 w-3 shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
