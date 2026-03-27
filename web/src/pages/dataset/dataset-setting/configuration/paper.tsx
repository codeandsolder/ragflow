import {
  AutoKeywordsFormField,
  AutoQuestionsFormField,
} from '@/components/form-fields/auto-keywords-form-field';
import { LayoutRecognizeFormField } from '@/components/form-fields/layout-recognize-form-field';
import {
  ConfigurationFormContainer,
  MainContainer,
} from '../configuration-form-container';
import { AutoMetadata } from './common-item';

export function PaperConfiguration() {
  return (
    <MainContainer>
      <ConfigurationFormContainer>
        <LayoutRecognizeFormField></LayoutRecognizeFormField>
      </ConfigurationFormContainer>

      <ConfigurationFormContainer>
        <AutoMetadata />
        <AutoKeywordsFormField></AutoKeywordsFormField>
        <AutoQuestionsFormField></AutoQuestionsFormField>
      </ConfigurationFormContainer>
      {/* <ConfigurationFormContainer>
        <TagItems></TagItems>
      </ConfigurationFormContainer> */}
    </MainContainer>
  );
}
