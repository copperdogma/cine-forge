export function formatCost(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value)
}

export function costLabel(complete: boolean, completeLabel: string): string {
  return complete ? completeLabel : 'Known estimated subtotal'
}
