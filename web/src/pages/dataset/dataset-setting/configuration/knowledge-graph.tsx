import { DelimiterFormField } from '@/components/form-fields/delimiter-form-field';
import { EntityTypesFormField } from '@/components/form-fields/entity-types-form-field';
import { MaxTokenNumberFormField } from '@/components/form-fields/max-token-number-from-field';

export function KnowledgeGraphConfiguration() {
  return (
    <>
      <>
        <EntityTypesFormField></EntityTypesFormField>
        <MaxTokenNumberFormField max={8192 * 2}></MaxTokenNumberFormField>
        <DelimiterFormField></DelimiterFormField>
      </>
    </>
  );
}
