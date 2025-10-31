export namespace main {
	
	export class FragmentMetadata {
	    text: string;
	    is_successful: boolean;
	    word_count: number;
	
	    static createFrom(source: any = {}) {
	        return new FragmentMetadata(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.text = source["text"];
	        this.is_successful = source["is_successful"];
	        this.word_count = source["word_count"];
	    }
	}
	export class TextFragment {
	    id: string;
	    filePath: string;
	    content: string;
	    wordCount: number;
	    displayName: string;
	
	    static createFrom(source: any = {}) {
	        return new TextFragment(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.filePath = source["filePath"];
	        this.content = source["content"];
	        this.wordCount = source["wordCount"];
	        this.displayName = source["displayName"];
	    }
	}

}

