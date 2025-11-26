/**
 * Truncate HTML string and keep tag safe.
 *
 * @param {String} string - string needs to be truncated
 * @param {Number} maxLength - length of truncated string
 * @param {Object} options - optional configuration
 * @param {Boolean} [options.keepImageTag] - flag to specify if keep image tag, false by default
 * @param {Boolean} [options.truncateLastWord] - truncates last word, true by default
 * @param {Number} [options.slop] - tolerance when options.truncateLastWord is false
 * @param {Boolean|String} [options.ellipsis] - omission symbol for truncated string, '...' by default
 * @return {String} truncated string
 */
export function truncateHTML(string, maxLength, options = {}) {
    const EMPTY_STRING = '';
    const DEFAULT_TRUNCATE_SYMBOL = '...';
    const DEFAULT_SLOP = 10 > maxLength ? maxLength : 10;
    const EXCLUDE_TAGS = ['img', 'br'];
    
    const items = [];
    let total = 0;
    let content = EMPTY_STRING;
    
    const KEY_VALUE_REGEX = '([\\w|-]+\\s*=\\s*"[^"]*"\\s*)*';
    const IS_CLOSE_REGEX = '\\s*\\/?\\s*';
    const CLOSE_REGEX = '\\s*\\/\\s*';
    const SELF_CLOSE_REGEX = new RegExp('<\\/?\\w+\\s*' + KEY_VALUE_REGEX + CLOSE_REGEX + '>');
    const HTML_TAG_REGEX = new RegExp('<\\/?\\w+\\s*' + KEY_VALUE_REGEX + IS_CLOSE_REGEX + '>');
    const URL_REGEX = /(((ftp|https?):\/\/)[\-\w@:%_\+.~#?,&\/\/=]+)|((mailto:)?[_.\w\-]+@([\w][\w\-]+\.)+[a-zA-Z]{2,3})/g;
    const IMAGE_TAG_REGEX = new RegExp('<img\\s*' + KEY_VALUE_REGEX + IS_CLOSE_REGEX + '>');
    const WORD_BREAK_REGEX = new RegExp('\\W+', 'g');
    
    let matches = true;

    options.ellipsis = (options.ellipsis !== undefined) ? options.ellipsis : DEFAULT_TRUNCATE_SYMBOL;
    options.truncateLastWord = (options.truncateLastWord !== undefined) ? options.truncateLastWord : true;
    options.slop = (options.slop !== undefined) ? options.slop : DEFAULT_SLOP;

    function removeImageTag(str) {
        const match = IMAGE_TAG_REGEX.exec(str);
        if (!match) return str;
        
        const index = match.index;
        const len = match[0].length;
        return str.substring(0, index) + str.substring(index + len);
    }

    function dumpCloseTag(tags) {
        let html = '';
        tags.reverse().forEach((tag) => {
            if (EXCLUDE_TAGS.indexOf(tag) === -1) {
                html += '</' + tag + '>';
            }
        });
        return html;
    }

    function getTag(str) {
        let tail = str.indexOf(' ');
        if (tail === -1) {
            tail = str.indexOf('>');
            if (tail === -1) {
                throw new Error('HTML tag is not well-formed : ' + str);
            }
        }
        return str.substring(1, tail);
    }

    function getEndPosition(str, tailPos) {
        const defaultPos = maxLength - total;
        let position = defaultPos;
        const isShort = defaultPos < options.slop;
        const slopPos = isShort ? defaultPos : options.slop - 1;
        const startSlice = isShort ? 0 : defaultPos - options.slop;
        const endSlice = tailPos || (defaultPos + options.slop);

        if (!options.truncateLastWord) {
            const substr = str.slice(startSlice, endSlice);

            if (tailPos && substr.length <= tailPos) {
                position = substr.length;
            } else {
                let result;
                while ((result = WORD_BREAK_REGEX.exec(substr)) !== null) {
                    if (result.index < slopPos) {
                        position = defaultPos - (slopPos - result.index);
                        if (result.index === 0 && defaultPos <= 1) break;
                    } else if (result.index === slopPos) {
                        position = defaultPos;
                        break;
                    } else {
                        position = defaultPos + (result.index - slopPos);
                        break;
                    }
                }
            }
            if (str.charAt(position - 1).match(/\s$/)) position--;
        }
        return position;
    }

    while (matches) {
        matches = HTML_TAG_REGEX.exec(string);

        if (!matches) {
            if (total >= maxLength) break;

            matches = URL_REGEX.exec(string);
            if (!matches || matches.index >= maxLength) {
                content += string.substring(0, getEndPosition(string));
                break;
            }

            while (matches) {
                const result = matches[0];
                const index = matches.index;
                content += string.substring(0, (index + result.length) - total);
                string = string.substring(index + result.length);
                matches = URL_REGEX.exec(string);
            }
            break;
        }

        const result = matches[0];
        const index = matches.index;

        if (total + index > maxLength) {
            content += string.substring(0, getEndPosition(string, index));
            break;
        } else {
            total += index;
            content += string.substring(0, index);
        }

        if (result[1] === '/') {
            items.pop();
        } else {
            const selfClose = SELF_CLOSE_REGEX.exec(result);
            if (!selfClose) {
                const tag = getTag(result);
                items.push(tag);
            }
            content += selfClose ? selfClose[0] : result;
        }

        string = string.substring(index + result.length);
    }

    if (string.length > maxLength - total && options.ellipsis) {
        content += options.ellipsis;
    }
    
    content += dumpCloseTag(items);

    if (!options.keepImageTag) {
        content = removeImageTag(content);
    }

    return content;
}
