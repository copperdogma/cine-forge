import { Input } from '@/components/ui/input'

export type BudgetSettingsFormState = {
  projectBudgetLimitUsd: string
  defaultRunBudgetLimitUsd: string
  budgetWarningThresholdRatio: string
}

type Props = {
  value: BudgetSettingsFormState
  onChange: (next: BudgetSettingsFormState) => void
}

export function ProjectBudgetSettingsSection({ value, onChange }: Props) {
  const update = (field: keyof BudgetSettingsFormState, nextValue: string) => {
    onChange({
      ...value,
      [field]: nextValue,
    })
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="project-budget-limit" className="text-sm font-medium">
          Project Budget Limit (USD)
        </label>
        <Input
          id="project-budget-limit"
          type="number"
          min="0"
          step="0.01"
          value={value.projectBudgetLimitUsd}
          onChange={(event) => update('projectBudgetLimitUsd', event.target.value)}
          placeholder="Leave blank for no cap"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="default-run-budget-limit" className="text-sm font-medium">
          Default Run Budget Limit (USD)
        </label>
        <Input
          id="default-run-budget-limit"
          type="number"
          min="0"
          step="0.01"
          value={value.defaultRunBudgetLimitUsd}
          onChange={(event) => update('defaultRunBudgetLimitUsd', event.target.value)}
          placeholder="Leave blank for no cap"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="budget-warning-threshold" className="text-sm font-medium">
          Budget Warning Threshold
        </label>
        <Input
          id="budget-warning-threshold"
          type="number"
          min="0"
          max="1"
          step="0.05"
          value={value.budgetWarningThresholdRatio}
          onChange={(event) => update('budgetWarningThresholdRatio', event.target.value)}
          placeholder="0.80"
        />
        <p className="text-xs text-muted-foreground">
          Enter a ratio between 0 and 1. Example: `0.80` warns at 80% of the cap.
        </p>
      </div>
    </div>
  )
}
