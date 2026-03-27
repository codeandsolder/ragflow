'use client';

import { SwitchFormField } from '@/components/form-fields/switch-fom-field';
import { TavilyFormField } from '@/components/form-fields/tavily-form-field';
import { TOCEnhanceFormField } from '@/components/form-fields/toc-enhance-form-field';
import { AvatarUpload } from '@/components/icons/avatar-upload';
import { KnowledgeBaseFormField } from '@/components/knowledge/knowledge-base-item';
import { MetadataFilter } from '@/components/metadata-filter';
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useTranslate } from '@/hooks/common-hooks';
import { getDirAttribute } from '@/utils/text-direction';
import { useFormContext } from 'react-hook-form';

export default function ChatBasicSetting() {
  const { t } = useTranslate('chat');
  const form = useFormContext();
  const nameValue = form.watch('name');
  const descriptionValue = form.watch('description');
  const emptyResponseValue = form.watch('prompt_config.empty_response');
  const prologueValue = form.watch('prompt_config.prologue');

  return (
    <div className="space-y-8">
      <FormField
        control={form.control}
        name={'icon'}
        render={({ field }) => (
          <div className="space-y-6">
            <FormItem className="w-full">
              <FormLabel>{t('assistantAvatar')}</FormLabel>
              <FormControl>
                <AvatarUpload {...field}></AvatarUpload>
              </FormControl>
              <FormMessage />
            </FormItem>
          </div>
        )}
      />
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel required>{t('assistantName')}</FormLabel>
            <FormControl>
              <Input {...field} dir={getDirAttribute(nameValue || '')}></Input>
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="description"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{t('description')}</FormLabel>
            <FormControl>
              <Textarea
                {...field}
                placeholder={t('descriptionPlaceholder')}
                dir={getDirAttribute(descriptionValue || '')}
              ></Textarea>
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={'prompt_config.empty_response'}
        render={({ field }) => (
          <FormItem>
            <FormLabel tooltip={t('emptyResponseTip')}>
              {t('emptyResponse')}
            </FormLabel>
            <FormControl>
              <Textarea
                {...field}
                placeholder={t('emptyResponsePlaceholder')}
                dir={getDirAttribute(emptyResponseValue || '')}
              ></Textarea>
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={'prompt_config.prologue'}
        render={({ field }) => (
          <FormItem>
            <FormLabel tooltip={t('setAnOpenerTip')}>
              {t('setAnOpener')}
            </FormLabel>
            <FormControl>
              <Textarea
                {...field}
                dir={getDirAttribute(prologueValue || '')}
              ></Textarea>
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <SwitchFormField
        name={'prompt_config.quote'}
        label={t('quote')}
        tooltip={t('quoteTip')}
      ></SwitchFormField>
      <SwitchFormField
        name={'prompt_config.keyword'}
        label={t('keyword')}
        tooltip={t('keywordTip')}
      ></SwitchFormField>
      <SwitchFormField
        name={'prompt_config.tts'}
        label={t('tts')}
        tooltip={t('ttsTip')}
      ></SwitchFormField>
      <TOCEnhanceFormField name="prompt_config.toc_enhance"></TOCEnhanceFormField>
      <TavilyFormField></TavilyFormField>
      <KnowledgeBaseFormField></KnowledgeBaseFormField>
      <MetadataFilter></MetadataFilter>
    </div>
  );
}
