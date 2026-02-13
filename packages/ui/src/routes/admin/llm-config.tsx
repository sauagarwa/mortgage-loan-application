import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { Bot, CheckCircle2, Loader2, Plus, XCircle, Zap } from 'lucide-react';
import { useAuth } from '../../auth/auth-provider';
import {
  useCreateLLMConfig,
  useLLMConfigs,
  useTestLLMConfig,
  useUpdateLLMConfig,
} from '../../hooks/admin';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import type { LLMProvider, LLMTestResult } from '../../schemas/admin';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/admin/llm-config' as any)({
  component: LLMConfigPage,
});

function LLMConfigPage() {
  const { hasRole } = useAuth();
  const { data: configs, isLoading } = useLLMConfigs();
  const updateConfig = useUpdateLLMConfig();
  const createConfig = useCreateLLMConfig();
  const testConfig = useTestLLMConfig();
  const [testResults, setTestResults] = useState<Record<string, LLMTestResult>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newProvider, setNewProvider] = useState({
    provider: '',
    base_url: '',
    api_key: '',
    default_model: '',
    max_tokens: 4096,
    temperature: 0.1,
    rate_limit_rpm: 60,
  });

  if (!hasRole('admin')) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Admin access required.</p>
      </div>
    );
  }

  const handleTest = async (provider: string) => {
    const result = await testConfig.mutateAsync(provider);
    setTestResults((prev) => ({ ...prev, [provider]: result }));
  };

  const handleSetDefault = (provider: string) => {
    updateConfig.mutate({ provider, data: { is_default: true } });
  };

  const handleToggleActive = (config: LLMProvider) => {
    updateConfig.mutate({
      provider: config.provider,
      data: { is_active: !config.is_active },
    });
  };

  const handleUpdateApiKey = (provider: string, apiKey: string) => {
    if (apiKey) {
      updateConfig.mutate({ provider, data: { api_key: apiKey } });
    }
  };

  const handleCreate = () => {
    createConfig.mutate(
      {
        ...newProvider,
        api_key: newProvider.api_key || undefined,
      },
      {
        onSuccess: () => {
          setShowAdd(false);
          setNewProvider({
            provider: '',
            base_url: '',
            api_key: '',
            default_model: '',
            max_tokens: 4096,
            temperature: 0.1,
            rate_limit_rpm: 60,
          });
        },
      },
    );
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">LLM Provider Configuration</h1>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAdd(!showAdd)}
        >
          <Plus className="mr-1 h-4 w-4" />
          Add Provider
        </Button>
      </div>

      {/* Add Provider Form */}
      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Add New Provider</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2">
              <input
                placeholder="Provider name (e.g., openai)"
                value={newProvider.provider}
                onChange={(e) =>
                  setNewProvider({ ...newProvider, provider: e.target.value })
                }
                className="rounded-md border bg-background px-3 py-2 text-sm"
              />
              <input
                placeholder="Base URL"
                value={newProvider.base_url}
                onChange={(e) =>
                  setNewProvider({ ...newProvider, base_url: e.target.value })
                }
                className="rounded-md border bg-background px-3 py-2 text-sm"
              />
              <input
                placeholder="API Key (optional)"
                type="password"
                value={newProvider.api_key}
                onChange={(e) =>
                  setNewProvider({ ...newProvider, api_key: e.target.value })
                }
                className="rounded-md border bg-background px-3 py-2 text-sm"
              />
              <input
                placeholder="Default Model"
                value={newProvider.default_model}
                onChange={(e) =>
                  setNewProvider({
                    ...newProvider,
                    default_model: e.target.value,
                  })
                }
                className="rounded-md border bg-background px-3 py-2 text-sm"
              />
            </div>
            <div className="mt-3 flex gap-2">
              <Button size="sm" onClick={handleCreate}>
                Create
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAdd(false)}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Provider Cards */}
      {isLoading ? (
        <p className="text-muted-foreground">Loading configurations...</p>
      ) : configs?.length === 0 ? (
        <p className="text-muted-foreground">
          No LLM providers configured. Click "Add Provider" to get started.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {configs?.map((config) => (
            <Card
              key={config.id}
              className={config.is_default ? 'border-primary' : ''}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    {config.provider}
                    {config.is_default && (
                      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                        Default
                      </span>
                    )}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggleActive(config)}
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        config.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                      }`}
                    >
                      {config.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Model:</span>{' '}
                    <span className="font-medium">{config.default_model}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Max Tokens:</span>{' '}
                    {config.max_tokens}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Temperature:</span>{' '}
                    {config.temperature}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Rate Limit:</span>{' '}
                    {config.rate_limit_rpm ?? 'N/A'} rpm
                  </div>
                  <div className="col-span-2">
                    <span className="text-muted-foreground">URL:</span>{' '}
                    <span className="font-mono text-xs">{config.base_url}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">API Key:</span>{' '}
                    {config.api_key_set ? (
                      <span className="text-green-600">Set</span>
                    ) : (
                      <span className="text-yellow-600">Not set</span>
                    )}
                  </div>
                </div>

                {/* API Key update */}
                <div className="flex gap-2">
                  <input
                    type="password"
                    placeholder="Update API key..."
                    className="flex-1 rounded-md border bg-background px-2 py-1 text-xs"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleUpdateApiKey(
                          config.provider,
                          (e.target as HTMLInputElement).value,
                        );
                        (e.target as HTMLInputElement).value = '';
                      }
                    }}
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTest(config.provider)}
                    disabled={testConfig.isPending}
                  >
                    {testConfig.isPending ? (
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                    ) : (
                      <Zap className="mr-1 h-3 w-3" />
                    )}
                    Test
                  </Button>
                  {!config.is_default && config.is_active && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSetDefault(config.provider)}
                    >
                      Set Default
                    </Button>
                  )}
                </div>

                {/* Test Result */}
                {testResults[config.provider] && (
                  <div
                    className={`flex items-center gap-2 rounded-md p-2 text-xs ${
                      testResults[config.provider].success
                        ? 'bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                        : 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                    }`}
                  >
                    {testResults[config.provider].success ? (
                      <CheckCircle2 className="h-3 w-3" />
                    ) : (
                      <XCircle className="h-3 w-3" />
                    )}
                    {testResults[config.provider].message}
                    {testResults[config.provider].latency_ms != null && (
                      <span className="ml-auto">
                        {testResults[config.provider].latency_ms}ms
                      </span>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
