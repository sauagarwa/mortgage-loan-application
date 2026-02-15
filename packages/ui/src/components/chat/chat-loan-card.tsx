import { Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../atoms/card/card';
import { Badge } from '../atoms/badge/badge';
import type { LoanCardData } from '../../schemas/chat';

interface ChatLoanCardProps {
  product: LoanCardData;
}

export function ChatLoanCard({ product }: ChatLoanCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{product.name}</CardTitle>
          <Badge variant="secondary" className="shrink-0 text-[10px]">
            {product.rate_type}
          </Badge>
        </div>
        {product.description && (
          <p className="text-xs text-muted-foreground">{product.description}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-muted-foreground">Term</span>
          <span className="font-medium">{product.term_years} years</span>
          {product.min_down_payment_pct !== null && (
            <>
              <span className="text-muted-foreground">Min Down</span>
              <span className="font-medium">{product.min_down_payment_pct}%</span>
            </>
          )}
          {product.min_credit_score !== null && (
            <>
              <span className="text-muted-foreground">Min Credit</span>
              <span className="font-medium">{product.min_credit_score}</span>
            </>
          )}
          {product.max_loan_amount !== null && (
            <>
              <span className="text-muted-foreground">Max Loan</span>
              <span className="font-medium">
                ${product.max_loan_amount.toLocaleString()}
              </span>
            </>
          )}
        </div>
        {product.features.length > 0 && (
          <div className="space-y-1 border-t pt-2">
            {product.features.map((feature, i) => (
              <div key={i} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                <Check className="mt-0.5 h-3 w-3 shrink-0 text-green-600" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
