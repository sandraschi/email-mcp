import DOMPurify from "dompurify";

type Props = {
	html: string;
	className?: string;
};

export function SanitizedHtml({ html, className }: Props) {
	return (
		<>
			<div
				className={className}
				// biome-ignore lint/security/noDangerouslySetInnerHtml: email HTML is sanitized with DOMPurify before render (XSS-safe)
				dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
			/>
		</>
	);
}
