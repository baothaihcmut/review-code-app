export default function ProblemPanel() {
  return (
    <div className="p-2 border rounded-md max-h-[200px] overflow-y-auto text-sm">
      <h2 className="font-semibold mb-1">Đề bài</h2>
      <pre className="whitespace-pre-wrap">
{`
Viết hàm void process(const char str[], char outstr[]) loại bỏ các khoảng trắng thừa trong chuỗi sao cho không còn hai khoảng trắng liền kề nhau và không có khoảng trắng nào ở đầu và cuối chuỗi.

- Đầu vào:

Mảng kí tự chứa chuỗi cần loại bỏ khoảng trắng

- Đầu ra:

Kết quả của bài toán được ghi vào chuỗi outstr

- Các thư viện có thể dùng: <iostream>, <cstring>

- Note: Sinh viên không được sử dụng các từ khoá sau trong đoạn code nộp bài, kể cả trong comment: "include", "string"

---------------------------------------

Implement void process(const char str[], char outstr[]) function which eliminates redundant space characters so that there are no consecutive space characters and there is no space character at the beginning/end of string.

- Input:

Char array contains the string

- Output:

The result is written to outstr

- Available library: <iostream>, <cstring>

- Note: Your code MUST NOT contain any of the words in the list {"include", "string"} even in the comment
`}
      </pre>
    </div>
  );
}
