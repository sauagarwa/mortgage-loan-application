import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { useAuth } from '../../auth/auth-provider';
import { useLoanProducts } from '../../hooks/loans';
import {
  useCreateApplication,
  useUpdateApplication,
  useSubmitApplication,
} from '../../hooks/applications';
import { Button } from '../../components/atoms/button/button';
import { Badge } from '../../components/atoms/badge/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { ArrowLeft, ArrowRight, Check, Send } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/applications/new' as any)({
  component: NewApplicationPage,
});

const STEPS = [
  { id: 'loan', title: 'Select Loan', description: 'Choose your loan product' },
  { id: 'personal', title: 'Personal Info', description: 'Your personal details' },
  { id: 'employment', title: 'Employment', description: 'Employment details' },
  { id: 'financial', title: 'Financial', description: 'Financial information' },
  { id: 'property', title: 'Property', description: 'Property details' },
  { id: 'declarations', title: 'Declarations', description: 'Legal declarations' },
  { id: 'review', title: 'Review & Submit', description: 'Review your application' },
];

function NewApplicationPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  const { data: loanProducts } = useLoanProducts();
  const createApplication = useCreateApplication();
  const [currentStep, setCurrentStep] = useState(0);
  const [applicationId, setApplicationId] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const [formData, setFormData] = useState({
    loan_product_id: (Route.useSearch() as { loanProductId?: string }).loanProductId || '',
    personal_info: {
      first_name: '',
      last_name: '',
      date_of_birth: '',
      ssn_last_four: '',
      email: '',
      phone: '',
      address: { street: '', city: '', state: '', zip_code: '' },
      citizenship_status: 'citizen',
    },
    employment_info: {
      employment_status: 'employed',
      employer_name: '',
      job_title: '',
      years_at_current_job: 0,
      years_in_field: 0,
      annual_income: 0,
      additional_income: 0,
      additional_income_source: '',
      is_self_employed: false,
    },
    financial_info: {
      credit_score_self_reported: 0,
      has_credit_history: true,
      monthly_debts: { car_loan: 0, student_loans: 0, credit_cards: 0, other: 0 },
      total_assets: 0,
      liquid_assets: 0,
      checking_balance: 0,
      savings_balance: 0,
      retirement_accounts: 0,
      investment_accounts: 0,
      bankruptcy_history: false,
      foreclosure_history: false,
    },
    property_info: {
      property_type: 'single_family',
      property_use: 'primary_residence',
      purchase_price: 0,
      down_payment: 0,
      address: { street: '', city: '', state: '', zip_code: '' },
    },
    declarations: {
      outstanding_judgments: false,
      party_to_lawsuit: false,
      federal_debt_delinquent: false,
      alimony_obligation: false,
      co_signer_on_other_loan: false,
      us_citizen: true,
      primary_residence: true,
    },
  });

  const updateApplication = useUpdateApplication(applicationId || '');
  const submitApplication = useSubmitApplication(applicationId || '');

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold">Sign In Required</h2>
          <p className="mb-6 text-muted-foreground">
            You need to sign in to create a mortgage application.
          </p>
          <Button onClick={login}>Sign In</Button>
        </div>
      </div>
    );
  }

  const updateField = (
    section: string,
    field: string,
    value: string | number | boolean,
  ) => {
    setFormData((prev) => ({
      ...prev,
      [section]: { ...(prev as Record<string, Record<string, unknown>>)[section], [field]: value },
    }));
  };

  const updateNestedField = (
    section: string,
    subsection: string,
    field: string,
    value: string | number,
  ) => {
    setFormData((prev) => {
      const sectionData = (prev as Record<string, Record<string, unknown>>)[section];
      const subData = sectionData[subsection] as Record<string, unknown>;
      return {
        ...prev,
        [section]: {
          ...sectionData,
          [subsection]: { ...subData, [field]: value },
        },
      };
    });
  };

  const handleNext = async () => {
    setErrors([]);

    // On first step, create the application draft
    if (currentStep === 0 && !applicationId) {
      if (!formData.loan_product_id) {
        setErrors(['Please select a loan product']);
        return;
      }
      try {
        const result = await createApplication.mutateAsync({
          loan_product_id: formData.loan_product_id,
        });
        setApplicationId(result.id);
        setCurrentStep((prev) => prev + 1);
      } catch (err) {
        setErrors([(err as Error).message]);
      }
      return;
    }

    // Auto-save on step transitions
    if (applicationId) {
      try {
        await updateApplication.mutateAsync({
          personal_info: formData.personal_info,
          employment_info: formData.employment_info,
          financial_info: formData.financial_info,
          property_info: formData.property_info,
          declarations: formData.declarations,
        });
      } catch {
        // Continue even if auto-save fails
      }
    }

    setCurrentStep((prev) => prev + 1);
  };

  const handleSubmit = async () => {
    if (!applicationId) return;
    setErrors([]);
    try {
      // Save final state
      await updateApplication.mutateAsync({
        personal_info: formData.personal_info,
        employment_info: formData.employment_info,
        financial_info: formData.financial_info,
        property_info: formData.property_info,
        declarations: formData.declarations,
      });
      // Submit
      await submitApplication.mutateAsync();
      navigate({ to: '/applications/$applicationId', params: { applicationId } });
    } catch (err) {
      setErrors([(err as Error).message]);
    }
  };

  const InputField = ({
    label,
    value,
    onChange,
    type = 'text',
    placeholder,
    required,
  }: {
    label: string;
    value: string | number;
    onChange: (val: string) => void;
    type?: string;
    placeholder?: string;
    required?: boolean;
  }) => (
    <div>
      <label className="mb-1 block text-sm font-medium">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>
      <input
        type={type}
        className="w-full rounded-md border bg-background px-3 py-2 text-sm"
        placeholder={placeholder}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );

  const SelectField = ({
    label,
    value,
    onChange,
    options,
  }: {
    label: string;
    value: string;
    onChange: (val: string) => void;
    options: { value: string; label: string }[];
  }) => (
    <div>
      <label className="mb-1 block text-sm font-medium">{label}</label>
      <select
        className="w-full rounded-md border bg-background px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );

  const CheckboxField = ({
    label,
    checked,
    onChange,
  }: {
    label: string;
    checked: boolean;
    onChange: (val: boolean) => void;
  }) => (
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        className="rounded border"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      {label}
    </label>
  );

  const renderStep = () => {
    switch (currentStep) {
      case 0: // Loan Selection
        return (
          <div className="space-y-4">
            {loanProducts?.items.map((loan) => (
              <div
                key={loan.id}
                onClick={() =>
                  setFormData((prev) => ({
                    ...prev,
                    loan_product_id: loan.id,
                  }))
                }
                className={`cursor-pointer rounded-lg border-2 p-4 transition-colors ${
                  formData.loan_product_id === loan.id
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="mb-1 flex items-center gap-2">
                      <span className="font-medium">{loan.name}</span>
                      <Badge variant="secondary">{loan.type}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {loan.description}
                    </p>
                  </div>
                  {formData.loan_product_id === loan.id && (
                    <Check className="h-5 w-5 text-primary" />
                  )}
                </div>
              </div>
            ))}
          </div>
        );

      case 1: // Personal Info
        return (
          <div className="grid gap-4 sm:grid-cols-2">
            <InputField label="First Name" value={formData.personal_info.first_name} onChange={(v) => updateField('personal_info', 'first_name', v)} required placeholder="John" />
            <InputField label="Last Name" value={formData.personal_info.last_name} onChange={(v) => updateField('personal_info', 'last_name', v)} required placeholder="Doe" />
            <InputField label="Email" value={formData.personal_info.email} onChange={(v) => updateField('personal_info', 'email', v)} type="email" required placeholder="john@example.com" />
            <InputField label="Phone" value={formData.personal_info.phone} onChange={(v) => updateField('personal_info', 'phone', v)} placeholder="+1-555-0123" />
            <InputField label="Date of Birth" value={formData.personal_info.date_of_birth} onChange={(v) => updateField('personal_info', 'date_of_birth', v)} type="date" />
            <InputField label="SSN (last 4)" value={formData.personal_info.ssn_last_four} onChange={(v) => updateField('personal_info', 'ssn_last_four', v)} placeholder="1234" />
            <div className="col-span-full">
              <p className="mb-2 text-sm font-medium">Address</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <InputField label="Street" value={formData.personal_info.address.street} onChange={(v) => updateNestedField('personal_info', 'address', 'street', v)} placeholder="123 Main St" />
                <InputField label="City" value={formData.personal_info.address.city} onChange={(v) => updateNestedField('personal_info', 'address', 'city', v)} placeholder="Springfield" />
                <InputField label="State" value={formData.personal_info.address.state} onChange={(v) => updateNestedField('personal_info', 'address', 'state', v)} placeholder="IL" />
                <InputField label="ZIP Code" value={formData.personal_info.address.zip_code} onChange={(v) => updateNestedField('personal_info', 'address', 'zip_code', v)} placeholder="62704" />
              </div>
            </div>
            <SelectField label="Citizenship Status" value={formData.personal_info.citizenship_status} onChange={(v) => updateField('personal_info', 'citizenship_status', v)} options={[
              { value: 'citizen', label: 'US Citizen' },
              { value: 'permanent_resident', label: 'Permanent Resident' },
              { value: 'visa_holder', label: 'Visa Holder' },
              { value: 'non_resident', label: 'Non-Resident' },
            ]} />
          </div>
        );

      case 2: // Employment
        return (
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField label="Employment Status" value={formData.employment_info.employment_status} onChange={(v) => updateField('employment_info', 'employment_status', v)} options={[
              { value: 'employed', label: 'Employed' },
              { value: 'self_employed', label: 'Self-Employed' },
              { value: 'retired', label: 'Retired' },
              { value: 'unemployed', label: 'Unemployed' },
              { value: 'student', label: 'Student' },
            ]} />
            <InputField label="Employer Name" value={formData.employment_info.employer_name} onChange={(v) => updateField('employment_info', 'employer_name', v)} placeholder="Acme Corp" />
            <InputField label="Job Title" value={formData.employment_info.job_title} onChange={(v) => updateField('employment_info', 'job_title', v)} placeholder="Software Engineer" />
            <InputField label="Years at Current Job" value={formData.employment_info.years_at_current_job} onChange={(v) => updateField('employment_info', 'years_at_current_job', Number(v))} type="number" />
            <InputField label="Years in Field" value={formData.employment_info.years_in_field} onChange={(v) => updateField('employment_info', 'years_in_field', Number(v))} type="number" />
            <InputField label="Annual Income ($)" value={formData.employment_info.annual_income} onChange={(v) => updateField('employment_info', 'annual_income', Number(v))} type="number" placeholder="95000" />
            <InputField label="Additional Income ($)" value={formData.employment_info.additional_income} onChange={(v) => updateField('employment_info', 'additional_income', Number(v))} type="number" />
            <InputField label="Additional Income Source" value={formData.employment_info.additional_income_source} onChange={(v) => updateField('employment_info', 'additional_income_source', v)} placeholder="Freelance" />
            <CheckboxField label="Self-employed" checked={formData.employment_info.is_self_employed} onChange={(v) => updateField('employment_info', 'is_self_employed', v)} />
          </div>
        );

      case 3: // Financial
        return (
          <div className="grid gap-4 sm:grid-cols-2">
            <InputField label="Credit Score (self-reported)" value={formData.financial_info.credit_score_self_reported} onChange={(v) => updateField('financial_info', 'credit_score_self_reported', Number(v))} type="number" placeholder="720" />
            <CheckboxField label="Has credit history" checked={formData.financial_info.has_credit_history} onChange={(v) => updateField('financial_info', 'has_credit_history', v)} />
            <div className="col-span-full">
              <p className="mb-2 text-sm font-medium">Monthly Debts</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <InputField label="Car Loan ($)" value={formData.financial_info.monthly_debts.car_loan} onChange={(v) => updateNestedField('financial_info', 'monthly_debts', 'car_loan', Number(v))} type="number" />
                <InputField label="Student Loans ($)" value={formData.financial_info.monthly_debts.student_loans} onChange={(v) => updateNestedField('financial_info', 'monthly_debts', 'student_loans', Number(v))} type="number" />
                <InputField label="Credit Cards ($)" value={formData.financial_info.monthly_debts.credit_cards} onChange={(v) => updateNestedField('financial_info', 'monthly_debts', 'credit_cards', Number(v))} type="number" />
                <InputField label="Other ($)" value={formData.financial_info.monthly_debts.other} onChange={(v) => updateNestedField('financial_info', 'monthly_debts', 'other', Number(v))} type="number" />
              </div>
            </div>
            <InputField label="Total Assets ($)" value={formData.financial_info.total_assets} onChange={(v) => updateField('financial_info', 'total_assets', Number(v))} type="number" />
            <InputField label="Liquid Assets ($)" value={formData.financial_info.liquid_assets} onChange={(v) => updateField('financial_info', 'liquid_assets', Number(v))} type="number" />
            <InputField label="Checking Balance ($)" value={formData.financial_info.checking_balance} onChange={(v) => updateField('financial_info', 'checking_balance', Number(v))} type="number" />
            <InputField label="Savings Balance ($)" value={formData.financial_info.savings_balance} onChange={(v) => updateField('financial_info', 'savings_balance', Number(v))} type="number" />
            <InputField label="Retirement Accounts ($)" value={formData.financial_info.retirement_accounts} onChange={(v) => updateField('financial_info', 'retirement_accounts', Number(v))} type="number" />
            <InputField label="Investment Accounts ($)" value={formData.financial_info.investment_accounts} onChange={(v) => updateField('financial_info', 'investment_accounts', Number(v))} type="number" />
            <CheckboxField label="Bankruptcy history" checked={formData.financial_info.bankruptcy_history} onChange={(v) => updateField('financial_info', 'bankruptcy_history', v)} />
            <CheckboxField label="Foreclosure history" checked={formData.financial_info.foreclosure_history} onChange={(v) => updateField('financial_info', 'foreclosure_history', v)} />
          </div>
        );

      case 4: // Property
        return (
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField label="Property Type" value={formData.property_info.property_type} onChange={(v) => updateField('property_info', 'property_type', v)} options={[
              { value: 'single_family', label: 'Single Family Home' },
              { value: 'condo', label: 'Condominium' },
              { value: 'townhouse', label: 'Townhouse' },
              { value: 'multi_family', label: 'Multi-Family (2-4 units)' },
              { value: 'manufactured', label: 'Manufactured Home' },
            ]} />
            <SelectField label="Property Use" value={formData.property_info.property_use} onChange={(v) => updateField('property_info', 'property_use', v)} options={[
              { value: 'primary_residence', label: 'Primary Residence' },
              { value: 'second_home', label: 'Second Home' },
              { value: 'investment', label: 'Investment Property' },
            ]} />
            <InputField label="Purchase Price ($)" value={formData.property_info.purchase_price} onChange={(v) => updateField('property_info', 'purchase_price', Number(v))} type="number" required placeholder="350000" />
            <InputField label="Down Payment ($)" value={formData.property_info.down_payment} onChange={(v) => updateField('property_info', 'down_payment', Number(v))} type="number" required placeholder="70000" />
            <div className="col-span-full">
              <p className="mb-2 text-sm font-medium">Property Address</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <InputField label="Street" value={formData.property_info.address.street} onChange={(v) => updateNestedField('property_info', 'address', 'street', v)} placeholder="456 Oak Ave" />
                <InputField label="City" value={formData.property_info.address.city} onChange={(v) => updateNestedField('property_info', 'address', 'city', v)} placeholder="Springfield" />
                <InputField label="State" value={formData.property_info.address.state} onChange={(v) => updateNestedField('property_info', 'address', 'state', v)} placeholder="IL" />
                <InputField label="ZIP Code" value={formData.property_info.address.zip_code} onChange={(v) => updateNestedField('property_info', 'address', 'zip_code', v)} placeholder="62701" />
              </div>
            </div>
          </div>
        );

      case 5: // Declarations
        return (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Please answer the following declarations truthfully. These are required
              for all mortgage applications.
            </p>
            <div className="space-y-3">
              <CheckboxField label="Do you have any outstanding judgments against you?" checked={formData.declarations.outstanding_judgments} onChange={(v) => updateField('declarations', 'outstanding_judgments', v)} />
              <CheckboxField label="Are you a party to any lawsuit?" checked={formData.declarations.party_to_lawsuit} onChange={(v) => updateField('declarations', 'party_to_lawsuit', v)} />
              <CheckboxField label="Are you delinquent on any federal debt?" checked={formData.declarations.federal_debt_delinquent} onChange={(v) => updateField('declarations', 'federal_debt_delinquent', v)} />
              <CheckboxField label="Do you have any alimony or child support obligations?" checked={formData.declarations.alimony_obligation} onChange={(v) => updateField('declarations', 'alimony_obligation', v)} />
              <CheckboxField label="Are you a co-signer on any other loan?" checked={formData.declarations.co_signer_on_other_loan} onChange={(v) => updateField('declarations', 'co_signer_on_other_loan', v)} />
              <CheckboxField label="Are you a US citizen?" checked={formData.declarations.us_citizen} onChange={(v) => updateField('declarations', 'us_citizen', v)} />
              <CheckboxField label="Will this be your primary residence?" checked={formData.declarations.primary_residence} onChange={(v) => updateField('declarations', 'primary_residence', v)} />
            </div>
          </div>
        );

      case 6: // Review
        return (
          <div className="space-y-6">
            <div>
              <h3 className="mb-2 text-sm font-medium uppercase text-muted-foreground">Personal Information</h3>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div><span className="text-muted-foreground">Name:</span> {formData.personal_info.first_name} {formData.personal_info.last_name}</div>
                <div><span className="text-muted-foreground">Email:</span> {formData.personal_info.email}</div>
                <div><span className="text-muted-foreground">Phone:</span> {formData.personal_info.phone || 'N/A'}</div>
                <div><span className="text-muted-foreground">Citizenship:</span> {formData.personal_info.citizenship_status}</div>
              </div>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium uppercase text-muted-foreground">Employment</h3>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div><span className="text-muted-foreground">Employer:</span> {formData.employment_info.employer_name || 'N/A'}</div>
                <div><span className="text-muted-foreground">Job Title:</span> {formData.employment_info.job_title || 'N/A'}</div>
                <div><span className="text-muted-foreground">Annual Income:</span> ${formData.employment_info.annual_income?.toLocaleString()}</div>
                <div><span className="text-muted-foreground">Years at Job:</span> {formData.employment_info.years_at_current_job}</div>
              </div>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium uppercase text-muted-foreground">Property</h3>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div><span className="text-muted-foreground">Purchase Price:</span> ${formData.property_info.purchase_price?.toLocaleString()}</div>
                <div><span className="text-muted-foreground">Down Payment:</span> ${formData.property_info.down_payment?.toLocaleString()}</div>
                <div><span className="text-muted-foreground">Loan Amount:</span> ${((formData.property_info.purchase_price || 0) - (formData.property_info.down_payment || 0)).toLocaleString()}</div>
                <div><span className="text-muted-foreground">Type:</span> {formData.property_info.property_type}</div>
              </div>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium uppercase text-muted-foreground">Financial</h3>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div><span className="text-muted-foreground">Credit Score:</span> {formData.financial_info.credit_score_self_reported || 'N/A'}</div>
                <div><span className="text-muted-foreground">Total Assets:</span> ${formData.financial_info.total_assets?.toLocaleString()}</div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-6 lg:p-8">
      <Link
        to="/dashboard"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      <h1 className="mb-6 text-2xl font-bold">New Mortgage Application</h1>

      {/* Step indicator */}
      <div className="mb-8 flex items-center gap-1 overflow-x-auto">
        {STEPS.map((step, i) => (
          <div key={step.id} className="flex items-center">
            <div
              className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ${
                i === currentStep
                  ? 'bg-primary text-primary-foreground'
                  : i < currentStep
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted text-muted-foreground'
              }`}
            >
              {i < currentStep ? (
                <Check className="h-3 w-3" />
              ) : (
                <span>{i + 1}</span>
              )}
              <span className="hidden sm:inline">{step.title}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`mx-1 h-px w-4 ${i < currentStep ? 'bg-primary' : 'bg-border'}`} />
            )}
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{STEPS[currentStep].title}</CardTitle>
          <CardDescription>{STEPS[currentStep].description}</CardDescription>
        </CardHeader>
        <CardContent>
          {errors.length > 0 && (
            <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {errors.map((err, i) => (
                <p key={i}>{err}</p>
              ))}
            </div>
          )}

          {renderStep()}

          <div className="mt-6 flex items-center justify-between">
            <Button
              variant="outline"
              onClick={() => setCurrentStep((prev) => prev - 1)}
              disabled={currentStep === 0}
            >
              <ArrowLeft className="h-4 w-4" />
              Previous
            </Button>

            {currentStep < STEPS.length - 1 ? (
              <Button
                onClick={handleNext}
                disabled={createApplication.isPending || updateApplication.isPending}
              >
                {createApplication.isPending
                  ? 'Saving...'
                  : 'Next'}
                <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitApplication.isPending}
              >
                {submitApplication.isPending
                  ? 'Submitting...'
                  : 'Submit Application'}
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
