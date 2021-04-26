silent! nunmap <Space>qf
silent! nunmap <Space>ac
silent! nunmap <Space>a
silent! nunmap <Space>f
silent! nunmap <Space>rn
silent! nunmap <Space>\
silent! nunmap <Space>-
silent! nunmap <Space>=
silent! nunmap <Space>clo
silent! nunmap <Space>clp
silent! nunmap <Space>cln
silent! nunmap <Space>co
silent! nunmap <Space>cp
silent! nunmap <Space>cn
silent! nunmap <Space>nt
silent! nunmap <Space>nf
silent! nunmap <Space>b
silent! nunmap <Space>w
silent! nunmap <Space>Q
silent! nunmap <Space>q
silent! nunmap <Space>s
silent! nunmap <Space>.
silent! nunmap <Space>l
silent! nunmap <Space>k
silent! nunmap <Space>j
silent! nunmap <Space>h
silent! nunmap <Space>

function Go()
    source LasersInc.nvim
    call LasersInc()
endfunction
nnoremap <silent> <C-g> :call Go()<CR>
silent! DisableWhitespace


