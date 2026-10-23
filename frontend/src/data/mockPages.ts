
export interface MockPage {
  page_number: number;
  page_type: "text_heavy" | "table" | "figure" | "mixed";
  probabilities: {
    text_heavy: number;
    table: number;
    figure: number;
    mixed: number;
  };
  used_ocr: boolean;
}

export const MOCK_PAGES: MockPage[] = Array.from(
  { length: 20 },
  (_, idx) => {
    const num = idx + 1;

    let pageType: MockPage["page_type"] = "text_heavy";
    let used_ocr = false;

    let probs = {
      text_heavy: 0.86,
      table: 0.04,
      figure: 0.03,
      mixed: 0.07,
    };

    if (num === 1) {
      pageType = "mixed";
      probs = {
        text_heavy: 0.22,
        table: 0.08,
        figure: 0.15,
        mixed: 0.55,
      };
    } else if (num === 4 || num === 9) {
      pageType = "figure";
      probs = {
        text_heavy: 0.12,
        table: 0.08,
        figure: 0.74,
        mixed: 0.06,
      };
    } else if (num === 8 || num === 14) {
      pageType = "table";
      probs = {
        text_heavy: 0.08,
        table: 0.81,
        figure: 0.04,
        mixed: 0.07,
      };
    } else if (num === 12 || num === 16) {
      pageType = "mixed";
      probs = {
        text_heavy: 0.25,
        table: 0.2,
        figure: 0.15,
        mixed: 0.4,
      };
    }

    if (num >= 18) {
      used_ocr = true;
      pageType = num === 19 ? "table" : "text_heavy";

      probs =
        num === 19
          ? {
              text_heavy: 0.15,
              table: 0.77,
              figure: 0.03,
              mixed: 0.05,
            }
          : {
              text_heavy: 0.84,
              table: 0.05,
              figure: 0.03,
              mixed: 0.08,
            };
    }

    return {
      page_number: num,
      page_type: pageType,
      probabilities: probs,
      used_ocr,
    };
  }
);
