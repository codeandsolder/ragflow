import {
  AutoKeywordsFormField,
  AutoQuestionsFormField,
} from '@/components/form-fields/auto-keywords-form-field';
import { ConfigurationFormContainer } from '../configuration-form-container';
import { AutoMetadata } from './common-item';

export function PictureConfiguration() {
  return (
    <ConfigurationFormContainer>
      <>
        <AutoMetadata />
        <AutoKeywordsFormField></AutoKeywordsFormField>
        <AutoQuestionsFormField></AutoQuestionsFormField>
      </>
      {/* <TagItems></TagItems> */}
    </ConfigurationFormContainer>
  );
}
