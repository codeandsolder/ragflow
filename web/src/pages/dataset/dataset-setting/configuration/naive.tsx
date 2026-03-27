import {
  AutoKeywordsFormField,
  AutoQuestionsFormField,
} from '@/components/form-fields/auto-keywords-form-field';
import { ChildrenDelimiterForm } from '@/components/form-fields/children-delimiter-form';
import { DelimiterFormField } from '@/components/form-fields/delimiter-form-field';
import { ExcelToHtmlFormField } from '@/components/form-fields/excel-to-html-form-field';
import { LayoutRecognizeFormField } from '@/components/form-fields/layout-recognize-form-field';
import { MaxTokenNumberFormField } from '@/components/form-fields/max-token-number-from-field';
import {
  ConfigurationFormContainer,
  MainContainer,
} from '../configuration-form-container';
import {
  AutoMetadata,
  EnableTocToggle,
  ImageContextWindow,
  OverlappedPercent,
} from './common-item';

export function NaiveConfiguration() {
  return (
    <MainContainer>
      <ConfigurationFormContainer>
        <LayoutRecognizeFormField testId="ds-settings-parser-pdf-parser-select"></LayoutRecognizeFormField>
        <MaxTokenNumberFormField
          initialValue={512}
          sliderTestId="ds-settings-parser-recommended-chunk-size-slider"
          numberInputTestId="ds-settings-parser-recommended-chunk-size-input"
        ></MaxTokenNumberFormField>
        <DelimiterFormField></DelimiterFormField>
        <ChildrenDelimiterForm />
        <EnableTocToggle />
        <ImageContextWindow />
        <AutoMetadata />
        <OverlappedPercent />
      </ConfigurationFormContainer>
      <ConfigurationFormContainer>
        <AutoKeywordsFormField></AutoKeywordsFormField>
        <AutoQuestionsFormField></AutoQuestionsFormField>
        <ExcelToHtmlFormField></ExcelToHtmlFormField>
        {/* <TagItems></TagItems> */}
      </ConfigurationFormContainer>
    </MainContainer>
  );
}
