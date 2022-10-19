

class ParseXItem:

    def __init__(self, xresponse):
        self.response = xresponse

    def parse_xsummary(self):

        EXCEPTION_SUMMARY = {}
        RAW_X_SUMMARY = (self.response.xpath('//div[@id="summary"]//tr'))

        for s in RAW_X_SUMMARY:
            values = []
            key = (s.xpath('.//th/text()').get()).strip(':')
            value = (s.xpath('.//td/text()').get())
            value_base = (s.xpath('.//td//span').get())
            span_flag = True if value_base\
                    and value_base is not None else False

            if span_flag:
                v = (s.xpath('.//td').get())
                v = v[v.find('class="fname">')+14:]
                value = v.replace('</span>','').replace('</td>','').strip()

            if not value or value is None:
                value = (s.xpath('.//td//pre/text()').get())

                if len(value.split('\n')) > 1:
                    for v in value.split('\n'):
                        values.append(
                            v.replace('[','').replace(']','').replace("'",'').replace(',','').strip()
                        )
                    value = values

            EXCEPTION_SUMMARY[key]=value

        return EXCEPTION_SUMMARY

