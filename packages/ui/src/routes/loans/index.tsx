import { createFileRoute, Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useLoanProducts } from '../../hooks/loans';
import { Badge } from '../../components/atoms/badge/badge';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { CheckCircle2, DollarSign } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/loans/' as any)({
  component: LoansPage,
});

const LOAN_TYPE_LABELS: Record<string, string> = {
  conventional: 'Conventional',
  fha: 'FHA',
  va: 'VA',
  usda: 'USDA',
  jumbo: 'Jumbo',
};

const LOAN_TYPE_FILTERS = [
  { value: '', label: 'All Types' },
  { value: 'conventional', label: 'Conventional' },
  { value: 'fha', label: 'FHA' },
  { value: 'va', label: 'VA' },
  { value: 'usda', label: 'USDA' },
  { value: 'jumbo', label: 'Jumbo' },
];

function LoansPage() {
  const [typeFilter, setTypeFilter] = useState('');
  const { data, isLoading } = useLoanProducts(
    typeFilter ? { type: typeFilter } : undefined,
  );

  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Mortgage Loan Products</h1>
        <p className="text-muted-foreground">
          Browse our available mortgage options and find the right fit for you.
        </p>
      </div>

      {/* Type filter */}
      <div className="mb-6 flex flex-wrap gap-2">
        {LOAN_TYPE_FILTERS.map((filter) => (
          <Button
            key={filter.value}
            variant={typeFilter === filter.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTypeFilter(filter.value)}
          >
            {filter.label}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-muted-foreground">
          Loading loan products...
        </div>
      ) : !data?.items.length ? (
        <div className="py-12 text-center text-muted-foreground">
          No loan products found.
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((loan) => (
            <Card key={loan.id} className="flex flex-col">
              <CardHeader>
                <div className="mb-2 flex items-center gap-2">
                  <Badge variant="secondary">
                    {LOAN_TYPE_LABELS[loan.type] ?? loan.type}
                  </Badge>
                  <Badge variant="outline">{loan.rate_type}</Badge>
                </div>
                <CardTitle className="text-lg">{loan.name}</CardTitle>
                <CardDescription>{loan.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Term</span>
                    <span className="font-medium">{loan.term_years} years</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      Min. Down Payment
                    </span>
                    <span className="font-medium">
                      {loan.min_down_payment_pct}%
                    </span>
                  </div>
                  {loan.min_credit_score && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        Min. Credit Score
                      </span>
                      <span className="font-medium">
                        {loan.min_credit_score}
                      </span>
                    </div>
                  )}
                  {loan.max_loan_amount && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        Max. Loan Amount
                      </span>
                      <span className="font-medium">
                        <DollarSign className="mr-0.5 inline h-3 w-3" />
                        {loan.max_loan_amount.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {loan.features.length > 0 && (
                    <div className="mt-4 border-t pt-3">
                      <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                        Features
                      </p>
                      <ul className="space-y-1.5">
                        {loan.features.slice(0, 3).map((feature, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-2 text-xs text-muted-foreground"
                          >
                            <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-green-500" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="gap-2">
                <Link
                  to="/loans/$loanId"
                  params={{ loanId: loan.id }}
                  className="flex-1"
                >
                  <Button variant="outline" className="w-full" size="sm">
                    Details
                  </Button>
                </Link>
                <Link
                  to="/applications/new"
                  search={{ loanProductId: loan.id }}
                  className="flex-1"
                >
                  <Button className="w-full" size="sm">
                    Apply Now
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
