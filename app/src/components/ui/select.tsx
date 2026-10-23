import * as SelectPrimitive from '@radix-ui/react-select'
import { CheckIcon, ChevronDownIcon, ChevronUpIcon } from '@radix-ui/react-icons'

type Option = { value: string; label: string }
export function Select({ id, value, onChange, options, placeholder, disabled, clearLabel }: { id: string; value: string; onChange: (value: string) => void; options: Option[]; placeholder: string; disabled?: boolean; clearLabel?: string }) {
  return <SelectPrimitive.Root value={value} onValueChange={value => onChange(value === '__clear' ? '' : value)} disabled={disabled}>
    <SelectPrimitive.Trigger id={id} className="select-trigger"><SelectPrimitive.Value placeholder={placeholder} /><SelectPrimitive.Icon><ChevronDownIcon /></SelectPrimitive.Icon></SelectPrimitive.Trigger>
    <SelectPrimitive.Portal><SelectPrimitive.Content className="select-menu" position="popper" sideOffset={8} collisionPadding={16}>
      <SelectPrimitive.ScrollUpButton className="select-scroll"><ChevronUpIcon /></SelectPrimitive.ScrollUpButton>
      <SelectPrimitive.Viewport className="select-options">{[...(clearLabel ? [{ value: '__clear', label: clearLabel }] : []), ...options].map(option => <SelectPrimitive.Item key={option.value} value={option.value} className="select-option"><SelectPrimitive.ItemText>{option.label}</SelectPrimitive.ItemText><SelectPrimitive.ItemIndicator><CheckIcon /></SelectPrimitive.ItemIndicator></SelectPrimitive.Item>)}</SelectPrimitive.Viewport>
      <SelectPrimitive.ScrollDownButton className="select-scroll"><ChevronDownIcon /></SelectPrimitive.ScrollDownButton>
    </SelectPrimitive.Content></SelectPrimitive.Portal>
  </SelectPrimitive.Root>
}
