import { Link } from '@tanstack/react-router';
import { Button } from '../atoms/button/button';
import { FileText, LogIn } from 'lucide-react';

export function Hero() {
  return (
    <section className="relative overflow-hidden rounded-2xl border bg-card p-6 shadow-sm sm:p-8">
      <div
        aria-hidden
        className="pointer-events-none absolute -inset-x-4 -top-16 bottom-0 opacity-60 [mask-image:radial-gradient(60%_60%_at_30%_0%,black,transparent)] dark:opacity-70"
      >
        <div className="mx-auto h-full max-w-6xl bg-gradient-to-tr from-sky-500/10 via-violet-500/10 to-fuchsia-500/10 blur-2xl" />
      </div>
      <div className="relative z-10 flex flex-col gap-4">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Welcome to Mortgage AI
        </h1>
        <div className="max-w-2xl space-y-2 text-sm leading-6 text-muted-foreground">
          <p>
            <strong>Applicants:</strong> Click <em>Apply Now</em> to start a new mortgage application.
            You can track your application status or view documents by logging in.
          </p>
          <p>
            <strong>Reviewers:</strong> Log in to review and manage mortgage applications.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 pt-1">
          <Link to="/chat">
            <Button size="lg">
              <FileText />
              Apply Now
            </Button>
          </Link>
          <Link to="/applications">
            <Button variant="outline" size="lg">
              <LogIn />
              Track My Application
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}