import {
  AutoKeywordsFormField,
  AutoQuestionsFormField,
} from '@/components/form-fields/auto-keywords-form-field';
import { LayoutRecognizeFormField } from '@/components/form-fields/layout-recognize-form-field';
import { ConfigurationFormContainer } from '../configuration-form-container';
import { AutoMetadata } from './common-item';

export function OneConfiguration() {
  return (
    <ConfigurationFormContainer>
      <LayoutRecognizeFormField></LayoutRecognizeFormField>
      <>
        <AutoMetadata />
        <AutoKeywordsFormField></AutoKeywordsFormField>
        <AutoQuestionsFormField></AutoQuestionsFormField>
      </>

      {/* <TagItems></TagItems> */}
    </ConfigurationFormContainer>
  );
}
