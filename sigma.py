#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int calculate_digit_sum(const char* str) {
    int sum = 0;
    for (int i = 0; str[i] != '\0'; i++) {
        char ch = str[i];

        if (ch >= '0' && ch <= '9') {
            int digit = ch - '0';
            sum += digit;
        }
    }
    return sum;
}

int main() {
    int length;
    char* str = NULL;

    printf("문자열의 길이를 입력하세요: ");
    if (scanf_s("%d", &length) != 1 || length <= 0) {
        printf("잘못된 길이 입력입니다.\n");
        return 1;
    }

    while (getchar() != '\n');

    str = (char*)malloc((length + 1) * sizeof(char));

    if (str == NULL) {
        printf("메모리 할당에 실패했습니다.\n");
        return 1;
    }

    printf("문자열 (최대 %d자)을 입력하세요: ", length);

    if (scanf_s("%s", str, length + 1) != 1) {
        printf("문자열 입력에 실패했습니다.\n");
        free(str);
        return 1;
    }

    int result_sum = calculate_digit_sum(str);

    printf("\n입력된 문자열: \"%s\"\n", str);
    printf("아라비아 숫자의 합계: %d\n", result_sum);

    free(str);
    str = NULL;

    return 0;
}