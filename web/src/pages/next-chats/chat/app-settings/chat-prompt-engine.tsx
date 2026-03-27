'use client';

import { CrossLanguageFormField } from '@/components/form-fields/cross-language-form-field';
import { SwitchFormField } from '@/components/form-fields/switch-fom-field';
import { TopNFormField } from '@/components/knowledge/top-n-item';
import { UseKnowledgeGraphFormField } from '@/components/knowledge/use-knowledge-graph-item';
import { RerankFormFields } from '@/components/rerank';
import { SimilaritySliderFormField } from '@/components/similarity-slider';
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import { useTranslate } from '@/hooks/common-hooks';
import { getDirAttribute } from '@/utils/text-direction';
import { useFormContext } from 'react-hook-form';
import { DynamicVariableForm } from './dynamic-variable';

export function ChatPromptEngine() {
  const { t } = useTranslate('chat');
  const form = useFormContext();
  const systemPromptValue = form.watch('prompt_config.system');

  return (
    <div className="space-y-8">
      <FormField
        control={form.control}
        name="prompt_config.system"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{t('system')}</FormLabel>
            <FormControl>
              <Textarea
                {...field}
                rows={8}
                placeholder={t('systemPlaceholder')}
                className="overflow-y-auto"
                dir={getDirAttribute(systemPromptValue || '')}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <SimilaritySliderFormField isTooltipShown></SimilaritySliderFormField>
      <TopNFormField></TopNFormField>
      <SwitchFormField
        name={'prompt_config.refine_multiturn'}
        label={t('multiTurn')}
        tooltip={t('multiTurnTip')}
      ></SwitchFormField>
      <UseKnowledgeGraphFormField name="prompt_config.use_kg"></UseKnowledgeGraphFormField>
      <RerankFormFields></RerankFormFields>
      <CrossLanguageFormField></CrossLanguageFormField>
      <DynamicVariableForm></DynamicVariableForm>
    </div>
  );
}
