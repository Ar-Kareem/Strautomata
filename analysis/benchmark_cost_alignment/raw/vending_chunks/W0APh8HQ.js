import"./CWj6FrbW.js";import{b7 as w,aq as v,b1 as k,b4 as T,bz as I,bs as x,a5 as i,bj as h,bv as N,bd as n,at as $,b0 as u}from"./BgSJMgn1.js";import{d as j,r as q,i as z,a as B}from"./ciYXbO5D.js";import{c as M,a as p,f as g}from"./Dj5dfjdS.js";import{e as P,f as V}from"./D0mkkeZb.js";import{C as X}from"./D2lNu8mi.js";import{s as A}from"./BYUezTe0.js";import{I as D}from"./B65QLH_c.js";function E(c,t){w(t,!0);/**
 * @license @lucide/svelte v0.548.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2023 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2025.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2023 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let o=q(t,["$$slots","$$events","$$legacy"]);const l=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];D(c,j({name:"copy"},()=>o,{get iconNode(){return l},children:(r,d)=>{var a=M(),m=v(a);A(m,()=>t.children??k),p(r,a)},$$slots:{default:!0}})),T()}var F=g("<!> <span>Copied</span>",1),G=g("<!> <span>Copy</span>",1),H=g('<section class="not-prose mt-16 mb-12"><h2 class="text-2xl mb-3">Citation</h2> <div class="relative"><pre class="overflow-x-auto rounded-lg bg-gray-100 px-5 py-4 pr-14 font-mono text-sm text-gray-800"> </pre> <button type="button" aria-label="Copy BibTeX" class="absolute top-3 right-3 inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-xs text-gray-700 hover:bg-gray-50 transition-colors"><!></button></div></section>');function W(c,t){let o=N(!1);async function l(){await navigator.clipboard.writeText(t.bibtex),h(o,!0),setTimeout(()=>h(o,!1),2e3)}var r=H(),d=x(i(r),2),a=i(d),m=i(a,!0);n(a);var b=x(a,2),y=i(b);{var _=e=>{var s=F(),f=v(s);X(f,{class:"w-3.5 h-3.5"}),u(2),p(e,s)},C=e=>{var s=G(),f=v(s);E(f,{class:"w-3.5 h-3.5"}),u(2),p(e,s)};z(y,e=>{$(o)?e(_):e(C,-1)})}n(b),n(d),n(r),I(()=>B(m,t.bibtex)),V("click",b,l),p(c,r)}P(["click"]);export{W as C};
